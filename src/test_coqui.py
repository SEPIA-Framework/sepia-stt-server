"""Test Coqui-STT"""

import argparse
import os
import json
from timeit import default_timer as timer
import wave

import numpy as np
from stt import Model

parser = argparse.ArgumentParser(description="Running Coqui-STT test inference.")
parser.add_argument("--wav", required=True, help="Path to WAV input file")
parser.add_argument("--model", required=True, help="Path to model folder")
parser.add_argument("--scorer", help="scorer file (inside model folder)")
parser.add_argument("--lm_alpha", type=float,
    help="Language model weight (lm_alpha). If not specified, use default from the scorer package.",
)
parser.add_argument("--lm_beta", type=float,
    help="Word insertion bonus (lm_beta). If not specified, use default from the scorer package.",
)
parser.add_argument("--beam_width", type=int, help="Beam width for CTC decoder")
parser.add_argument("--hot_words", type=str, help="Hot-words and their boosts.")
parser.add_argument("--extended", action="store_true",
    help="Output string from extended metadata",
)
parser.add_argument("--plain", action="store_true",
    help="Output plain text for final resilt instead of JSON with timestamp of each word",
)
parser.add_argument("--alternatives", type=int, default=1,
    help="Number of alternative transcripts to include in JSON output",
)
args = parser.parse_args()
# Coqui can't handle alternatives=0
args.alternatives = max(1, args.alternatives)

#----------------------------

def collect_words_list(transcript):
    """Collect words from transcript as list of dicts"""
    _word = ""
    _word_list = []
    _word_start_time = 0
    # Loop through each character
    for i, token in enumerate(transcript.tokens):
        # Append character to word if it's not a space
        if token.text != " ":
            if len(_word) == 0:
                # Log the start time of the new word
                _word_start_time = token.start_time
            _word = _word + token.text
        # Word boundary is either a space or the last character in the array
        if token.text == " " or i == len(transcript.tokens) - 1:
            word_duration = max(token.start_time - _word_start_time, 0)
            each_word = dict()
            each_word["word"] = _word
            each_word["start"] = round(_word_start_time, 4)
            each_word["end"] = round(_word_start_time + word_duration, 4)
            _word_list.append(each_word)
            # Reset
            _word = ""
            _word_start_time = 0
    return _word_list

def transcript_to_string(transcript):
    """Convert transcript to string"""
    return "".join(token.text for token in transcript.tokens)

def metadata_to_json(metadata):
    """Convert metadata to JSON"""
    json_result = dict()
    json_result["transcripts"] = [
        {
            "confidence": transcript.confidence,
            "words": collect_words_list(transcript),
        }
        for transcript in metadata.transcripts
    ]
    return json_result

#----------------------------

model_file = f"{args.model}/model.tflite"
scorer_file = f"{args.model}/{args.scorer}" if args.scorer else None
if not os.path.exists(model_file):
    print (f"The model file '{model_file}' does not exist.")
    exit (1)
if scorer_file and not os.path.exists(scorer_file):
    print (f"The scorer file '{scorer_file}' does not exist.")
    exit (1)

wf = wave.open(args.wav, "rb")
sample_rate_orig = wf.getframerate()
audio_length = wf.getnframes() * (1 / sample_rate_orig)
if (wf.getnchannels() != 1 or wf.getsampwidth() != 2
    or wf.getcomptype() != "NONE" or sample_rate_orig != 16000):
    print ("Audio file must be WAV format mono PCM.")
    exit (1)

print("Loading model")
model_load_start = timer()
rec = Model(model_file)
print("Loaded in {:.3}s.".format(timer() - model_load_start))

if args.beam_width:
    rec.setBeamWidth(args.beam_width)

if scorer_file:
    print("Loading scorer from files {}".format(scorer_file))
    scorer_load_start = timer()
    rec.enableExternalScorer(scorer_file)
    print("Loaded scorer in {:.3}s.".format(timer() - scorer_load_start))

if args.lm_alpha and args.lm_beta:
    rec.setScorerAlphaBeta(args.lm_alpha, args.lm_beta)

if args.hot_words:
    print("Adding hot-words")
    for word_boost in args.hot_words.split(","):
        word, boost = word_boost.split(":")
        rec.addHotWord(word, float(boost))

print("Running inference.")
inference_start = timer()
stream_rec = rec.createStream()
while True:
    data = np.frombuffer(wf.readframes(4000), dtype=np.int16)
    if len(data) == 0:
        if args.plain:
            print(stream_rec.finishStream())
        else:
            print(json.dumps(metadata_to_json(
                stream_rec.finishStreamWithMetadata(args.alternatives)), indent=2))
        break
    else:
        stream_rec.feedAudioContent(data)
        if args.plain:
            print(stream_rec.intermediateDecode())
        else:
            partial = stream_rec.intermediateDecodeWithMetadata(num_results=1)
            print(transcript_to_string(partial.transcripts[0]).strip())
#stream_rec.freeStream()

#static:
#audio = np.frombuffer(wf.readframes(wf.getnframes()), np.int16)
#if args.extended:
#    print(transcript_to_string(rec.sttWithMetadata(audio, 1).transcripts[0]))
#elif args.json:
#    print(json.dumps(metadata_to_json(
#        rec.sttWithMetadata(audio, args.alternatives)), indent=2))
#else:
#    print(rec.stt(audio))

print("Inference took {:.3}s for {:.3}s audio file.".format(
    timer() - inference_start, audio_length))
wf.close()
