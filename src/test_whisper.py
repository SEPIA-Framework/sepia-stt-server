#!/usr/bin/env python3

import argparse
import os
from timeit import default_timer as timer
import wave

import numpy as np
from faster_whisper import WhisperModel

# Arguments
parser = argparse.ArgumentParser(description="Running Whisper test inference.")
parser.add_argument("-w", "--wav", required=True, help="Path to WAV input file")
parser.add_argument("-m", "--model", required=True, help="Path to the model")
parser.add_argument("-l", "--lang", default="auto", help="Language used (default: auto)")
parser.add_argument("--beamsize", default=1, help="Beam size used (default: 1)")
parser.add_argument("--prompt", default=None, help="Initial prompt (default: None)")
parser.add_argument("--translate", action="store_true", help="Translate to 'en' (default: false)")
parser.add_argument("--words", action="store_true", help="Get word-level ts and confidence (default: false)")
parser.add_argument("--vad", action="store_true", help="Use VAD to filter silence (>2s by default).")
parser.add_argument("--fp32", action="store_true", help="Use float32 compute type for models.")
parser.add_argument("-t", "--threads", default=2, help="Threads used (default: 2)")
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

# run on CPU:

print(f'\nLoading model {model_path} ...')
compute_type = "float32" if args.fp32 else "int8"
model_load_start = timer()
model = WhisperModel(
    model_path,
    device="cpu",
    compute_type=compute_type,
    cpu_threads=int(args.threads)
)
#model = WhisperModel(args.model, device="cuda", compute_type="float16")
print(f'Threads: {args.threads}')
print(f'Beam size: {args.beamsize}')
print(f'Compute type: {compute_type}')
print(f"Loaded in {(timer() - model_load_start):.2f}s.")

def transcribe(audio_array_or_file):
    """Run inference for audio file or bytes"""
    inference_start = timer()
    print("\nTranscribing ...")

    segments = None
    info = None
    segments, info = model.transcribe(
        audio_array_or_file,
        beam_size=int(args.beamsize),
        language=args.lang if args.lang != "auto" else None,
        initial_prompt=args.prompt,
        task="transcribe" if not args.translate else "translate",
        word_timestamps=args.words,
        vad_filter=args.vad
    )
    if args.lang == "auto":
        print(f"Detected language '{info.language}' with "
              + f"probability {info.language_probability:.3f}")

    if segments is not None:
        print("Result:")
        for segment in segments:
            if args.words:
                for word in segment.words:
                    print(f"[{word.start:.2f}s -> {word.end:.2f}s] "
                          + f"{word.word} (conf.: {word.probability:.2f}s)")
            else:
                print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

        print(f"\nInference took {(timer() - inference_start):.2f}s "
              + f"for {audio_length:.2f}s audio file.")

# for demo purposes we read the wav in chunks
byte_stream = bytearray()
chunk_size = 4096
while True:
    audio_bytes = wf.readframes(chunk_size)
    #audio_bytes = wf.readframes(wf.getnframes())
    if len(audio_bytes) == 0:
        break
    else:
        byte_stream += audio_bytes
# convert to Whisper compatible float 32 numpy array
audio_ndarray_int16 = np.frombuffer(byte_stream, dtype=np.int16)
audio_ndarray_f32 = audio_ndarray_int16.astype(np.float32) / 32768.0

transcribe(audio_ndarray_f32)
wf.close()
