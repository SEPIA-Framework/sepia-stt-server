"""ASR engine module for Coqui: https://github.com/coqui-ai/STT"""

import os
import json

import numpy as np
from stt import Model

from launch import settings
from engine_interface import EngineInterface, ModelNotFound
from text_processor import TextToNumberProcessor, DateAndTimeOptimizer

class CoquiProcessor(EngineInterface):
    """Process chunks with Coqui"""
    def __init__(self, send_message, options: dict = None):
        """Create Coqui processor"""
        # Get all common options and defaults
        super().__init__(send_message, options)
        # Specific options:
        # -- scorer (LM file) relative to: settings.asr_models_folder
        self._asr_model_scorer = options.get("scorer", None)
        # -- typically shared options
        self._alternatives = options.get("alternatives", int(1))
        self._return_words = options.get("words", False)
        # -- increase probability of certain words
        self._hot_words = options.get("hot_words", [])
        # example: self._phrase_list = [{word: "timer", boost: 1.5}]
        # Recognizer
        asr_model_path = settings.asr_models_folder + self._asr_model_path
        asr_model_file = (f"{asr_model_path}/model.tflite") # NOTE: currently we assume tflite
        asr_scorer_file = (f"{asr_model_path}/{self._asr_model_scorer}"
            if self._asr_model_scorer else None)
        # Make sure paths exist and load models
        if not os.path.exists(asr_model_file):
            raise ModelNotFound(f"ASR model file seems to be wrong: {asr_model_file}")
        if asr_scorer_file and not os.path.exists(asr_scorer_file):
            raise RuntimeError(f"ASR scorer file seems to be wrong: {asr_scorer_file}")
        self._model = Model(asr_model_file)
        if asr_scorer_file:
            self._model.enableExternalScorer(asr_scorer_file)
        # Use hot words?
        # if self._phrase_list and len(self._phrase_list) > 0:
        # create
        self._recognizer = self._model.createStream()
        self._partial_result = {}
        self._last_partial_str = ""
        self._final_result = {}
        # states - 0: waiting for input, 1: got partial result, 2: got final result, 3: closing
        self._state = 0
        # internal helpers
        self._silence_energy = 0    # Coqui does not emit final results after "silence", we do that
        self._silence_threshold = 5 # If enery is >= threshold we start a new result
        #
        # TODO: GPU support ?

    def get_partial_result(self, chunk: bytes):
        """Get partial result of first transcript (ignore alternatives)"""
        self._recognizer.feedAudioContent(chunk)
        partial_transcript = self._recognizer.intermediateDecodeWithMetadata(
            num_results=1).transcripts[0]
        return "".join(token.text for token in partial_transcript.tokens)

    async def process(self, chunk: bytes):
        """Feed audio chunks to recognizer"""
        np_chunk = np.frombuffer(chunk, dtype=np.int16)
        result = None
        if self._state == 3:
            pass
        elif chunk and len(chunk) > 0:
            self._recognizer.feedAudioContent(np_chunk)
            # Partial result and silence check
            result = self._recognizer.intermediateDecodeWithMetadata(num_results=1)
            if result:
                self._state = 1
                await self._handle_partial_result(result)

        if self._silence_energy >= self._silence_threshold:
            # Silence detected
            result = self._recognizer.finishStreamWithMetadata(num_results=self._alternatives)
            self._state = 2
            self._silence_energy = 0
            await self._handle_final_result(result)
            # Create new recognizer and feed last chunk so we don't miss stuff
            self._recognizer = self._model.createStream() # create a new one
            self._recognizer.feedAudioContent(np_chunk)

    async def finish_processing(self):
        """Wait for last process and end"""
        # End?
        await self._finish()

    async def close(self):
        """Reset recognizer and remove"""
        #if self._recognizer:
            #self._recognizer.freeStream()   # this will throw an error if closed already
            #self._recognizer = None

    def get_options(self):
        """Get Coqui options for active setup"""
        active_options = {
            "language": self._language,
            "model": self._asr_model_path,
            "scorer": self._asr_model_scorer,
            "samplerate": self._sample_rate,
            "optimizeFinalResult": self._optimize_final_result,
            "alternatives": self._alternatives,
            "continuous": self._continuous_mode,
            "words": self._return_words
        }
        if self._hot_words and len(self._hot_words) > 0:
            # NOTE: this can be very large, for now we use a placeholder
            active_options["hot_words"] = []
            #active_options["hot_words"] = self._hot_words
        else:
            active_options["hot_words"] = []
        return active_options

    async def _handle_partial_result(self, result):
        """Handle a partial result"""
        partial_str = CoquiProcessor.transcript_to_string(result.transcripts[0])
        # Same as last time?
        if partial_str == self._last_partial_str:
            self._silence_energy += 1
        else:
            self._silence_energy = 0
            self._last_partial_str = partial_str
            norm_result = CoquiProcessor.normalize_result_format(
                result, self._alternatives, self._return_words)
            self._partial_result = norm_result
            #print("PARTIAL: ", self._partial_result)
            await self._send(self._partial_result, False)

    async def _handle_final_result(self, result, skip_send = False):
        """Handle a final result"""
        if result:
            #print("FINAL: ", result)
            norm_result = CoquiProcessor.normalize_result_format(
                result, self._alternatives, self._return_words)
            if self._continuous_mode:
                # In continous mode we send "intermediate" final results
                self._final_result = norm_result
                if not skip_send:
                    await self._send(self._final_result, True)
            else:
                # In non-continous mode we remember one big result
                self._final_result = CoquiProcessor.append_to_result(self._final_result, norm_result)
            #print("FINAL (auto): ", self._final_result)

    async def _finish(self):
        """Tell recognizer to stop and handle last result"""
        last_result_was_final = (self._state == 2)
        self._state = 3
        if last_result_was_final and not self._continuous_mode:
            # Send final result (because we haven't done it yet)
            await self._send(self._final_result, True)
            # TODO: destroy recognizer?
        elif last_result_was_final:
            # TODO: destroy recognizer?
            pass
        else:
            # Request final
            result = self._recognizer.finishStreamWithMetadata(num_results=self._alternatives)
            await self._handle_final_result(result, skip_send=True)
            await self._send(self._final_result, True)

    async def _send(self, json_result, is_final = False):
        """Send result"""
        features = {}
        alternatives = []
        if self._return_words:
            features["words"] = json_result.get("words", [])
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
    def transcript_to_string(transcript):
        """Convert transcript to string"""
        return "".join(token.text for token in transcript.tokens)

    @staticmethod
    def normalize_result_format(result: str, alternatives = 0, has_words = False):
        """Coqui format adaptation"""
        words = None
        # TODO: fix for Coqui
        if alternatives > 0 and "alternatives" in json_result:
            json_result = json_result.get("alternatives", [])
            # handle array
            alternatives = None
            if len(json_result) > 1:
                alternatives = json_result[1:]
            if has_words:
                words = json_result[0].get("result")
            return CoquiProcessor.build_normalized_result(json_result[0],
                alternatives, words)
        else:
            # handle object
            if has_words:
                words = json_result.get("result")
            return CoquiProcessor.build_normalized_result(json_result,
                None, words)

    @staticmethod
    def build_normalized_result(json_result, alternatives = None, words = None):
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
            result["words"] = words
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
            return given_result
        else:
            new_result["text"] = text
            return new_result
