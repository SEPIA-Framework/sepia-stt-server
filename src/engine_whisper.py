"""ASR engine module for Whisper: https://github.com/guillaumekln/faster-whisper"""

import os
#import json
import logging
from typing import List
from timeit import default_timer as timer

from uvicorn.config import logger

import numpy as np

from faster_whisper.utils import get_logger
from faster_whisper import WhisperModel
from faster_whisper.vad import get_speech_timestamps

from launch_setup import settings
from engine_interface import EngineInterface, ModelNotFound

# faster_whisper log level
whisper_logger = get_logger()
if settings.log_level == "error":
    whisper_logger.setLevel(logging.ERROR)
elif settings.log_level == "warning":
    whisper_logger.setLevel(logging.WARNING)
elif settings.log_level == "debug":
    whisper_logger.setLevel(logging.DEBUG)
else:
    whisper_logger.setLevel(logging.INFO)

class WhisperCachedModel:
    """Class for cached Whisper models"""
    def __init__(self, model: WhisperModel, path: str):
        self.model = model
        self.path = path
        self.in_use: bool = False

# global session and model tracking
CACHED_MODELS: List[WhisperCachedModel] = []
MAX_CACHE_SIZE: int = settings.whisper_model_cache_size
THREADS_PER_MODEL: int = settings.whisper_threads_per_model

def get_or_create_model(
        model_path: str,
        model_properties: dict = {},
        options: dict = {}
    ):
    """Get model from cache or create a new one
    if there is space left"""
    full_model_path = settings.asr_models_folder + model_path
    # Make sure paths exist and check global cache
    if not os.path.exists(full_model_path):
        raise ModelNotFound("ASR model path seems to be wrong")
    cached_model: WhisperCachedModel = next((model for model in CACHED_MODELS
        if model.path == model_path and not model.in_use), None)
    if not cached_model:
        # not cached (yet)
        if len(CACHED_MODELS) >= MAX_CACHE_SIZE:
            raise RuntimeError("Too many active Whisper models! Exceeded cache size.")
        else:
            compute_device = model_properties.get("compute_device", "cpu")
            compute_type = model_properties.get("compute_type", "int8")
            new_model = WhisperModel(
                full_model_path,
                device = compute_device,
                compute_type = compute_type,
                cpu_threads = THREADS_PER_MODEL
            )
            cached_model = WhisperCachedModel(new_model, model_path)
            CACHED_MODELS.append(cached_model)
            return cached_model
    else:
        # found in cache
        return cached_model


class WhisperResult():
    """Result of Whisper encoder + decoder"""
    def __init__(self,
            text: List[str],
            text_conf: List[float],
            words: List[dict],
            duration_s: float
        ):
        self.text: List[str] = text
        self.text_conf: List[float] = text_conf
        self.words: List[dict] = words
        self.duration_s = duration_s


class WhisperProcessor(EngineInterface):
    """Process chunks with Whisper (faster-whisper)"""

    def __init__(self, send_message, options: dict = None):
        """Create Whisper processor"""
        # Get all common options and defaults
        super().__init__(send_message, options)
        # Specific options:
        if options is None:
            options = {}
        # -- no optimization required for Whisper
        self._optimize_final_result = False
        # -- typically shared options
        self._return_words = options.get("words", options.get("words_ts", False))
        # -- beamsize
        self._beamsize = options.get("beamsize", None)
        if not self._beamsize and "beamsize" in self._asr_model_properties:
            self._beamsize = self._asr_model_properties["beamsize"]
        elif not self._beamsize:
            self._beamsize = 1
        # -- initial prompt (runtime option and model setting)
        self._init_prompt = options.get("prompt", options.get("init_prompt", None))
        if not self._init_prompt and "prompt" in self._asr_model_properties:
            self._init_prompt = self._asr_model_properties["prompt"]
        # -- translate to english (runtime option and model setting)
        do_translate = options.get("translate")
        if do_translate is None and "translate" in self._asr_model_properties:
            do_translate = self._asr_model_properties["translate"]
        if do_translate is True or str(do_translate).lower() in ['true', 'yes']:
            self._translate = True
        else:
            self._translate = False
        # NOTE: translation should probably disable word timestamps
        if self._translate:
            self._return_words = False
        # Model
        self._model: WhisperCachedModel = get_or_create_model(
            model_path=self._asr_model_path,
            model_properties=self._asr_model_properties,
            options=options
        )
        self._model.in_use = True

        self._final_result = {}
        # states - 0: waiting for input, 1: tbd, 2: got final result, 3: closing
        self._state = 0
        self._is_processing = False

        self._chunk_buffer: np.ndarray[np.float32] = None
        self._samples_per_sec_fp32 = self._sample_rate
        self._min_buffer_size_fp32 = self._sample_rate * 2 # min-size for VAD check (2s in fp32)
        self._chunk_total_int16: int = 0
        self._last_buffer_split_at: int = 0

        self._max_duration_s = 30
        self._measured_rtf = 0
        self._process_queue_size = 0

        # 3-step dynamic min-silence to optimize long audio split (for continuous mode)
        self._dynamic_min_silence_ms = [1750, 1000, 500]
        self._dynamic_min_silence_thresh = [0, 10, 20]

    async def process(self, chunk: bytes):
        """Process chunks"""
        if self._state == 3:
            pass
        try:
            # collect chunks
            self._chunk_total_int16 += len(chunk)
            if self._chunk_buffer is None:
                self._chunk_buffer = WhisperProcessor.int16_to_float32_ndarray(chunk)
            else:
                self._chunk_buffer = np.concatenate(
                    (self._chunk_buffer, WhisperProcessor.int16_to_float32_ndarray(chunk)),
                    axis=0
                )
            # check if processor is blocked
            if self._is_processing:
                self._process_queue_size += 1
                logger.warning("WhisperProcessor - "
                    + f"Inference is slow! Last RTF: {self._measured_rtf:.2f}")
            # VAD processing
            elif self._chunk_buffer.size >= self._min_buffer_size_fp32:
                await self._process_with_vad()

        except OSError:
            logger.exception("WhisperProcessor - Failed to process")
            self.on_error("Engine: whisper - Message: Failed to process")
            self._clean_up_recognizer()

    async def finish_processing(self):
        """Wait for last process and end"""
        try:
            await self._finish()
        except OSError:
            logger.exception("WhisperProcessor - Failed to finish process")
            self.on_error("Engine: whisper - Message: Failed to finish process")
            self._clean_up_recognizer()

    async def close(self):
        """Clean up and close"""
        await self.on_before_close()
        self._clean_up_recognizer()

    def get_options(self):
        """Get processor options"""
        active_options = {
            "language": self._language,
            "task": self._asr_task,
            "model": self._asr_model_name,
            "samplerate": self._sample_rate,
            "optimizeFinalResult": self._optimize_final_result,
            "continuous": self._continuous_mode,
            "words": self._return_words,
            "beamsize": self._beamsize,
            "prompt": self._init_prompt,
            "translate": self._translate
        }
        return active_options


    async def _send(self, json_result, is_final = False):
        """Send result"""
        features = {}
        alternatives = []
        if self._return_words:
            features["words"] = json_result.get("words", [])
        transcript = json_result.get("text", "")
        await self.send_transcript(
            transcript=transcript,
            is_final=is_final,
            confidence=json_result.get("confidence", -1),
            features=features,
            alternatives=alternatives)

    def _process_result(self, segments, info):
        """Process all segments. Optionally runs encoder first then decodes tokens."""
        # check inference speed
        if self._continuous_mode and self._process_queue_size >= 3:
            # queue is too large now
            logger.exception("WhisperProcessor - "
                + f"Inference is too slow for continuous mode! Last RTF: {self._measured_rtf:.2f}")
            self.on_error("Engine: whisper - Message: Inference is too slow for continuous mode.")
            raise RuntimeError("Whisper inference is too slow for continuous mode!")
        text: List[str] = []
        text_conf: List[float] = []
        words: List[dict] = []
        if segments is not None:
            for segment in segments:
                #print("segmnet", segment)  # DEBUG
                if not segment.no_speech_prob or segment.no_speech_prob < 0.7:
                    # TODO: fix time offsets for continuous mode
                    if self._return_words:
                        for word in segment.words:
                            # word: start, end, word, probability
                            #print(f"{word.word} (conf.: {word.probability:.2fs})")  # DEBUG
                            words.append({
                                "start": word.start,
                                "end": word.end,
                                "word": word.word,
                                "confidence": word.probability
                            })
                    if segment.text:
                        # segment: id, seek, start, end, text, tokens, temperature
                        #   avg_logprob, compression_ratio, no_speech_prob, words
                        #print(f"{segment.text}")  # DEBUG
                        text.append(segment.text.strip())
                        text_conf.append(segment.avg_logprob)
        return WhisperResult(
            text=text,
            text_conf=text_conf,
            words=words,
            duration_s=info.duration
        )

    async def _handle_final_result(self, whisp_res: WhisperResult, skip_send = False):
        """Handle a final result"""
        #result = {
        #    "text": text,
        #    "confidence": confidence,
        #    "alternatives": alternatives,
        #    "words": [{
        #      "start": 1.41,
        #      "end": 1.89,
        #      "word": "dialog",
        #      "confidence": 0.90
        #    }, ...]
        #}
        has_data = False
        if whisp_res.text:
            self._final_result["text"] = " ".join(whisp_res.text)
            # confidence: naive average of logprobs (TODO: improve):
            avg_text_conf_naive = sum(whisp_res.text_conf)/len(whisp_res.text_conf)
            self._final_result["confidence"] = avg_text_conf_naive
            has_data = True
        if whisp_res.words:
            self._final_result["words"] = whisp_res.words
            has_data = True
        if has_data:
            self._final_result["duration"] = whisp_res.duration_s
            if not skip_send:
                await self._send(self._final_result, True)

    async def _transcribe(self, process_chunks):
        """Transcribe float32 chunks in ndarray"""
        # require at least 500ms of audio
        if process_chunks.size > self._samples_per_sec_fp32 // 2:
            #audio_length_s = process_chunks.size / self._samples_per_sec_fp32
            #print(f"processing {audio_length_s:.2f}s of audio")
            self._is_processing = True
            inference_start = timer()
            # mel-spectrum and optionally encoding
            segments, info = self._model.model.transcribe(
                process_chunks,
                beam_size=int(self._beamsize),
                language=self.language_code_short,
                initial_prompt=self._init_prompt,
                word_timestamps=self._return_words,
                task="transcribe" if not self._translate else "translate",
                temperature=0,  # TODO: temporary fix for "Segmentation fault"
                vad_filter=False
            )
            # encoding (if None) and finally decoding
            whisper_res: WhisperResult = self._process_result(segments, info)
            # ready
            self._is_processing = False
            inference_time = timer() - inference_start
            self._measured_rtf = inference_time/info.duration
            #print(f"inference time: {inference_time:.2f}s - RTF: {self._measured_rtf}")
            self._state = 0
            await self._handle_final_result(whisper_res)
        else:
            self._state = 0

    def _get_vad_result(self, duration_s = None):
        """Get VAD result with timestamps for speech"""
        if duration_s is None:
            duration_s = self._chunk_buffer.size / self._samples_per_sec_fp32
        if self._continuous_mode:
            # 3-step dynamic min-silence
            if duration_s >= self._dynamic_min_silence_thresh[2]:
                min_silence = self._dynamic_min_silence_ms[2]
            elif duration_s >= self._dynamic_min_silence_thresh[1]:
                min_silence = self._dynamic_min_silence_ms[1]
            else:
                min_silence = self._dynamic_min_silence_ms[0]
        else:
            # Fixed min-silence
            min_silence = self._dynamic_min_silence_ms[0]
        speech_ts = get_speech_timestamps(
            audio = self._chunk_buffer,
            #threshold: float = 0.5,
            #min_speech_duration_ms: int = 250,
            #max_speech_duration_s: float = float("inf"),
            min_silence_duration_ms = min_silence
            #window_size_samples: int = 1024,
            #speech_pad_ms: int = 400,
        )
        return speech_ts

    async def _split_chunks_and_process(self, start_chunk_i, end_chunk_i):
        """Split buffer and process first"""
        self._state = 2
        process_chunks = self._chunk_buffer[start_chunk_i:end_chunk_i]
        self._chunk_buffer = self._chunk_buffer[end_chunk_i:]
        self._last_buffer_split_at = self._chunk_total_int16
        await self._transcribe(process_chunks)

    def _split_chunks_to_reduce_buffer(self):
        """Get rid of some silence in buffer to reduce size"""
        last_2s_chunks = -2 * self._samples_per_sec_fp32
        self._chunk_buffer = self._chunk_buffer[last_2s_chunks:]

    async def _process_with_vad(self):
        """Process chunk buffer to see if we can get a result"""
        #print(f"len chunks: {self._chunk_buffer.size}")   # DEBUG
        duration_s = self._chunk_buffer.size / self._samples_per_sec_fp32
        speech_ts = self._get_vad_result(duration_s)
        if duration_s > self._max_duration_s:
            # force buffer clean-up
            start_chunk_i = 0
            end_chunk_i = self._chunk_buffer.size
            await self._split_chunks_and_process(start_chunk_i, end_chunk_i)
            logger.warning("WhisperProcessor - Reached max length for "
                + f"single segment: {self._max_duration_s}s")
            # TODO: can we fix transition to next chunk by context transfer?
        # Do we have more than one speech block?
        elif len(speech_ts) > 1:
            # take everything from 0-start to n-1 end
            start_chunk_i = speech_ts[0]["start"]
            end_chunk_i = speech_ts[-1]["end"]
            await self._split_chunks_and_process(start_chunk_i, end_chunk_i)
        # Do we have enough silence? (TODO: or total length?)
        elif len(speech_ts) == 1:
            start_chunk_i = speech_ts[0]["start"]
            end_chunk_i = speech_ts[0]["end"]
            #current_chunk_int16 = self._chunk_total_int16 - self._last_buffer_split_at
            if end_chunk_i + self._samples_per_sec_fp32 <= self._chunk_buffer.size:
                await self._split_chunks_and_process(start_chunk_i, end_chunk_i)
        # Can we reduce buffer size?
        elif self._chunk_buffer.size > self._samples_per_sec_fp32 * 4:
            self._split_chunks_to_reduce_buffer()

    async def _finish(self):
        """Tell recognizer to stop and handle last result"""
        # transcribe rest - TODO: check VAD before?
        self._state = 3
        # require at least 500ms of audio
        if self._chunk_buffer.size > self._samples_per_sec_fp32 // 2:
            # check VAD first
            speech_ts = self._get_vad_result()
            if len(speech_ts) >= 1:
                await self._transcribe(self._chunk_buffer)
        self._model.in_use = False
        return True

    def _clean_up_recognizer(self):
        """Reset some variables and states after error"""
        if self._model is not None:
            self._model.in_use = False
        if self._chunk_buffer is not None:
            self._chunk_buffer = None
        self._is_processing = False

    # ---- Helper functions ----

    @staticmethod
    def int16_to_float32_ndarray(chunk):
        """Convert int16 audio chunks to float32 numpy array"""
        int16_nda = np.frombuffer(chunk, dtype=np.int16)
        f32_nda = int16_nda.astype(np.float32) / 32768.0
        return f32_nda
