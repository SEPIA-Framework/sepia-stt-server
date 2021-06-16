"""ASR engine module for Vosk: https://github.com/alphacep/vosk-api"""

import os
import json

from vosk import Model, SpkModel, KaldiRecognizer

from launch import settings
from engine_interface import EngineInterface

class VoskProcessor(EngineInterface):
    """Process chunks with Vosk"""
    def __init__(self, send_message, options = None):
        """Create Vosk processor"""
        super().__init__(send_message)
        # Options
        language = None
        phrase_list = None
        #phrase_list = ["hallo", "kannst du mich hören", "[unk]"]
        if options is not None:
            language = options["language"]
            phrase_list = options["phrase_list"]
        # Recognizer - TODO: check options for language and switch model
        asr_model_path = settings.asr_model_paths[0]        #"../models/vosk-model-small-de"
        spk_model_path = settings.speaker_model_paths[0]    #"../models/vosk-model-spk"
        if not os.path.exists(asr_model_path):
            raise RuntimeError("ASR model path seems to be wrong")
        if settings.has_speaker_detection and not os.path.exists(spk_model_path):
            raise RuntimeError("Speaker model path seems to be wrong")
        self._model = Model(asr_model_path)
        if settings.has_speaker_detection:
            self._spk_model = SpkModel(spk_model_path)
        self._sample_rate = float(16000)
        self._alternatives = int(0)
        if phrase_list is not None and len(phrase_list) > 0:
            self._recognizer = KaldiRecognizer(self._model, self._sample_rate, 
                json.dumps(phrase_list, ensure_ascii=False))
        else:
            self._recognizer = KaldiRecognizer(self._model, self._sample_rate)
        self._recognizer.SetMaxAlternatives(self._alternatives)
        #self._recognizer.SetWords(True)
        if settings.has_speaker_detection:
            self._recognizer.SetSpkModel(self._spk_model)
        self._partial_result = ""
        self._final_result = ""
        #
        # TODO: GPU support: check Vosk examples to find out how to enable GPU ... :-P
        # from vosk import GpuInit, GpuInstantiate ...
        # https://github.com/alphacep/vosk-api/tree/master/python/example

    async def process(self, chunk: bytes):
        """Feed audio chunks to recognizer"""
        result = None
        if self._recognizer.AcceptWaveform(chunk):
            result = self._recognizer.Result()
        else:
            result = self._recognizer.PartialResult()
            if result != self._partial_result:
                self._partial_result = result
                print("PARTIAL: ", self._partial_result)
                await self.send_transcript(self._partial_result, False)
        # End?
        #if not self.accept_chunks:
        #    await self._finish()

    async def finish_processing(self):
        """Wait for last process and end"""
        # End?
        await self._finish()

    async def close(self):
        pass

    async def _finish(self):
        self._final_result = self._recognizer.FinalResult()
        print("FINAL: ", self._final_result)
        if self._final_result is not None:
            await self.send_transcript(self._final_result, True)
