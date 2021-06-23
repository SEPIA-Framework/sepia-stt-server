# SEPIA Speech-To-Text Server

SEPIA Speech-To-Text (STT) Server is a WebSocket based, full-duplex Python server for realtime automatic speech recognition (ASR) supporting multiple open-source ASR engines.
It can receive a stream of audio chunks via the secure WebSocket connection and return transcribed text almost immediately as partial and final results.  
  
One goal of this project is to offer a **standardized, secure, realtime interface** for all the great open-source ASR tools out there.
The server works on all major platforms including single-board devices like Raspberry Pi (4).  
  
NOTE: This is **V2** of the STT Server, for V1 please see the [LEGACY SERVER](legacy-server) folder.

## Features

* WebSocket server (Python Fast-API) that can receive audio streams and send transcribed text at the same time
* Modular architecture to support multiple ASR engines like Vosk (reference implementation), Coqui, Deepspeech, Scribosermo, ...
* Standardized API for all engines and support for individual engine features (speaker identification, grammar, confidence score, word timestamps, alternative results, etc.)
* On-the-fly server and engine configuration via HTTP REST API and WebSocket 'welcome' event
* User authentication via simple common token or individual tokens for multiple users
* Docker containers with support for all major platform architectures: x86 64Bit (amd64), ARM 32Bit (armv7l) and ARM 64Bit (aarch64)
* Fast enough to run even on Raspberry Pi 4 (2GB) in realtime (depending on engine and model configuration)
* Compatible to [SEPIA Framework client](https://github.com/SEPIA-Framework/sepia-html-client-app)

## Quick-Start

Coming soon ...