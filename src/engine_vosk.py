"""ASR engine module for Vosk: https://github.com/alphacep/vosk-api"""

import os
import json

from vosk import Model, SpkModel, KaldiRecognizer, SetLogLevel

from launch import settings
from engine_interface import EngineInterface, ModelNotFound
from text_processor import TextToNumberProcessor, DateAndTimeOptimizer

# Vosk log level - -1: off, 0: normal, 1: more verbose
SetLogLevel(-1)

class VoskProcessor(EngineInterface):
    """Process chunks with Vosk"""
    def __init__(self, send_message, options: dict = None):
        """Create Vosk processor"""
        # Get all common options and defaults
        super().__init__(send_message, options)
        # Specific options
        # -- typically shared options
        # NOTE: difference between alternatives 0 and 1 is only the Vosk result format!
        self._alternatives = options.get("alternatives", int(1))
        self._return_words = options.get("words", False)
        # -- list of custom phrases to recognize
        # example: self._phrase_list = ["hallo", "kannst du mich hören", "[unk]"]
        self._phrase_list = options.get("phrases")
        # -- speaker detection
        try_speaker_detection = options.get("speaker", False)
        # NOTE: speaker detection does not work in all configurations
        if try_speaker_detection:
            self._speaker_detection = (settings.has_speaker_detection_model
                and self._alternatives == 0)
        else:
            self._speaker_detection = False
        # Recognizer
        asr_model_path = settings.asr_models_folder + self._asr_model_path
        # Speaker model
        spk_model_path = settings.speaker_models_folder + settings.speaker_model_paths[0]
        # Make sure paths exist and load models
        if not os.path.exists(asr_model_path):
            raise ModelNotFound("ASR model path seems to be wrong")
        if self._speaker_detection and not os.path.exists(spk_model_path):
            raise RuntimeError("Speaker model path seems to be wrong")
        self._model = Model(asr_model_path)
        if self._speaker_detection:
            self._spk_model = SpkModel(spk_model_path)
        # Use phrase list?
        if self._phrase_list and len(self._phrase_list) > 0:
            self._recognizer = KaldiRecognizer(self._model, self._sample_rate,
                json.dumps(self._phrase_list, ensure_ascii=False))
        else:
            self._recognizer = KaldiRecognizer(self._model, self._sample_rate)
        self._recognizer.SetMaxAlternatives(self._alternatives)
        if self._return_words:
            self._recognizer.SetWords(True)
        if self._speaker_detection:
            self._recognizer.SetSpkModel(self._spk_model)
        self._partial_result = {}
        self._last_partial_str = ""
        self._final_result = {}
        # states - 0: waiting for input, 1: got partial result, 2: got final result, 3: closing
        self._state = 0
        #
        # TODO: GPU support: check Vosk examples to find out how to enable GPU ... :-P
        # Example code:
        # from vosk import GpuInit, GpuInstantiate
        # GpuInit()
        # def thread_init():
        #     GpuInstantiate()
        # pool = concurrent.futures.ThreadPoolExecutor(initializer=thread_init)

    async def process(self, chunk: bytes):
        """Feed audio chunks to recognizer"""
        result = None
        if self._state == 3:
            pass
        elif self._recognizer.AcceptWaveform(chunk):
            # Silence detected
            result = self._recognizer.Result()
            self._state = 2
            await self._handle_final_result(result)
        else:
            # Partial results possible
            result = self._recognizer.PartialResult()
            self._state = 1
            await self._handle_partial_result(result)
        # End?
        #if not self.accept_chunks:
        #    await self._finish()

    async def finish_processing(self):
        """Wait for last process and end"""
        # End?
        await self._finish()

    async def close(self):
        """Reset recognizer and remove"""
        #if self._recognizer:
            #self._recognizer.Reset()   # this throws an error!? Maye because its closed already?
            #self._recognizer = None

    def get_options(self):
        """Get Vosk options for active setup"""
        active_options = {
            "language": self._language,
            "model": self._asr_model_name,
            "samplerate": self._sample_rate,
            "optimizeFinalResult": self._optimize_final_result,
            "alternatives": self._alternatives,
            "continuous": self._continuous_mode,
            "words": self._return_words,
            "speaker": self._speaker_detection
        }
        if self._phrase_list and len(self._phrase_list) > 0:
            # NOTE: this can be very large, for now we use a placeholder
            active_options["phrases"] = []
            #active_options["phrases"] = self._phrase_list
        else:
            active_options["phrases"] = []
        return active_options

    async def _handle_partial_result(self, result):
        """Handle a partial result"""
        if result and self._last_partial_str != result:
            self._last_partial_str = result
            # Note: we disable words and alt. for partial results (not supported anyway)
            norm_result = VoskProcessor.normalize_result_format(
                result, alternatives = int(1), return_words = False)
            self._partial_result = norm_result
            #print("PARTIAL: ", self._partial_result)
            await self._send(self._partial_result, False)

    async def _handle_final_result(self, result, skip_send = False):
        """Handle a final result"""
        if result:
            #print("FINAL: ", result)
            norm_result = VoskProcessor.normalize_result_format(
                result, self._alternatives, self._return_words)
            if self._continuous_mode:
                # In continuous mode we send "intermediate" final results
                self._final_result = norm_result
                if not skip_send:
                    await self._send(self._final_result, True)
            else:
                # In non-continuous mode we remember one big result
                self._final_result = VoskProcessor.append_to_result(self._final_result, norm_result)
            #print("FINAL (auto): ", self._final_result)

    async def _finish(self):
        """Tell recognizer to stop and handle last result"""
        last_result_was_final = (self._state == 2)
        self._state = 3
        if last_result_was_final and not self._continuous_mode:
            # Send final result (because we haven't done it yet)
            await self._send(self._final_result, True)
            # self._recognizer.Reset()  # TODO: we skip this to prevent ERROR if already reset
        elif last_result_was_final:
            # We don't need to do anything but reset ... right?
            # self._recognizer.Reset()  # TODO: we skip this to prevent ERROR if already reset
            pass
        else:
            # Request final
            result = self._recognizer.FinalResult()
            await self._handle_final_result(result, skip_send=True)
            await self._send(self._final_result, True)

    async def _send(self, json_result, is_final = False):
        """Send result"""
        features = {}
        alternatives = []
        if self._return_words:
            features["words"] = json_result.get("words", [])
        if self._speaker_detection:
            features["speaker_vector"] = json_result.get("spk", [])
        if self._alternatives > 0:
            alternatives = json_result.get("alternatives", [])
        transcript = json_result.get("text", "")
        # Post-processing?
        if is_final and transcript and self._optimize_final_result:
            # Optimize final transcription
            text2num_proc = TextToNumberProcessor(self._language)
            dt_optimizer = DateAndTimeOptimizer(self._language)
            transcript = text2num_proc.process(transcript)
            transcript = dt_optimizer.process(transcript)
        await self.send_transcript(
            transcript=transcript,
            is_final=is_final,
            confidence=json_result.get("confidence", -1),
            features=features,
            alternatives=alternatives)

    # ---- Helper functions ----

    @staticmethod
    def normalize_result_format(result: str, alternatives: int = 0, return_words = False):
        """Vosk has many different formats depending on settings
        Convert result into a fixed format so we can handle it better"""
        json_result = json.loads(result)
        words = None
        if alternatives > 0 and "alternatives" in json_result:
            # When alternatives is set the result format is different!
            json_result = json_result.get("alternatives", [])
            # handle array
            alternatives_list = None
            if len(json_result) > 1:
                alternatives_list = json_result[1:]
            if return_words:
                words = json_result[0].get("result")
            return VoskProcessor.build_normalized_result(json_result[0],
                alternatives_list, words)
        else:
            # handle object
            if return_words:
                words = json_result.get("result")
            return VoskProcessor.build_normalized_result(json_result,
                None, words)

    @staticmethod
    def build_normalized_result(json_result: dict, alternatives: list = None, words = None):
        """Build a result object that always looks the same"""
        # text or partial or empty:
        text = json_result.get("text", json_result.get("partial", json_result.get("final", "")))
        confidence = json_result.get("confidence", -1)
        speaker_vec = json_result.get("spk")
        result = {
            "text": text,
            "confidence": confidence,
            "alternatives": alternatives
        }
        if words is not None:
            result["words"] = words # NOTE: currently we only return words of first transcript
        if speaker_vec is not None:
            result["spk"] = speaker_vec
        return result

    @staticmethod
    def append_to_result(given_result, new_result):
        """Append a new result to a previous one, typically used for
        'intermediate' final result text"""
        text = new_result.get("text")
        if not text:
            return given_result
        #else:            # we can do more post-processing here maybe
        if "text" in given_result:
            given_result["text"] += ", " + text
            if "confidence" in new_result:
                # sloppy confidence merge (take the worst)
                given_result["confidence"] = min(
                    given_result.get("confidence", -1), new_result.get("confidence", -1))
            if "words" in new_result:
                # append words
                given_words = given_result.get("words", [])
                new_words = new_result.get("words", [])
                if given_words and len(given_words) and new_words and len(new_words):
                    given_result["words"] = given_words + new_words
            if "spk" in new_result:
                # take new speaker data - NOTE: not optimal
                given_result["spk"] = new_result.get("spk", given_result.get("spk", []))
            return given_result
        else:
            new_result["text"] = text
            return new_result
