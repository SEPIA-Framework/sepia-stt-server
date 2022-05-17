#!/usr/bin/env python3

import argparse
import os
from timeit import default_timer as timer
import wave

from vosk import Model, KaldiRecognizer, SetLogLevel

# Vosk log level:
SetLogLevel(0)

# Arguments
parser = argparse.ArgumentParser(description="Running Vosk test inference.")
parser.add_argument("--wav", required=True, help="Path to WAV input file")
parser.add_argument("--model", required=True, help="Path to the model")
parser.add_argument("--alternatives", type=int, default=0,
    help="Number of alternative transcripts to include in JSON output",
)
parser.add_argument("--words", action="store_true",
    help="Show each word with timestamp",
)
args = parser.parse_args()

model_path = args.model
if not os.path.exists(model_path):
    print ("The model folder'", model_path, "'does not exist.")
    exit (1)

wf = wave.open(args.wav, "rb")
sample_rate_orig = wf.getframerate()
audio_length = wf.getnframes() * (1 / sample_rate_orig)
if (wf.getnchannels() != 1 or wf.getsampwidth() != 2
    or wf.getcomptype() != "NONE" or sample_rate_orig != 16000):
    print ("Audio file must be WAV format, 16000 Hz, mono, PCM.")
    exit (1)

print("Loading model and recognizer")
model_load_start = timer()
model = Model(model_path)
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetWords(args.words)    # NOTE: only for 1 result ?
rec.SetMaxAlternatives(args.alternatives)
print("Loaded in {:.3}s.".format(timer() - model_load_start))

print("Running inference.")
inference_start = timer()
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        print(rec.Result())
    else:
        print(rec.PartialResult())

print(rec.FinalResult())
print("Inference took {:.3}s for {:.3}s audio file.".format(
    timer() - inference_start, audio_length))
wf.close()
