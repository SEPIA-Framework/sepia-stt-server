# SEPIA Speech-To-Text Server

SEPIA Speech-To-Text (STT) Server is a WebSocket based, full-duplex Python server for realtime automatic speech recognition (ASR) supporting multiple open-source ASR engines.
It can receive a stream of audio chunks via the secure WebSocket connection and return transcribed text almost immediately as partial and final results.  
  
One goal of this project is to offer a **standardized, secure, realtime interface** for all the great open-source ASR tools out there.
The server works on all major platforms including single-board devices like Raspberry Pi (4).  
  
NOTE: This is **V2** of the STT Server, for V1 please see the [LEGACY SERVER](legacy-server) folder. 
If you are using custom V1 models you can easily [convert them to V2 models](https://github.com/fquirin/kaldi-adapt-lm/blob/master/4a-build-vosk-model.sh) (please ask for details via the issues section).

## Features

* WebSocket server (Python Fast-API) that can receive audio streams and send transcribed text at the same time
* Modular architecture to support multiple ASR engines like Vosk (reference implementation), Coqui, Deepspeech, Scribosermo, ...
* Optional post processing of result (e.g. via [text2num](https://github.com/allo-media/text2num))
* Standardized API for all engines and support for individual engine features (speaker identification, grammar, confidence score, word timestamps, alternative results, etc.)
* On-the-fly server and engine configuration via HTTP REST API and WebSocket 'welcome' event (including custom grammar, if supported by engine and model)
* User authentication via simple common token or individual tokens for multiple users
* Docker containers with support for all major platform architectures: x86 64Bit (amd64), ARM 32Bit (armv7l) and ARM 64Bit (aarch64)
* Fast enough to run even on Raspberry Pi 4 (2GB) in realtime (depending on engine and model configuration)
* Compatible to [SEPIA Framework client](https://github.com/SEPIA-Framework/sepia-html-client-app) (v0.24+)

## Integrated ASR Engines

- [Vosk](https://github.com/alphacep/vosk-api) - Status: Included (with tiny EN and DE model)
- [Coqui](https://github.com/coqui-ai/STT) - Status: Planned.
- [Scribosermo](https://gitlab.com/Jaco-Assistant/Scribosermo) - Status: Help wanted.
- If you want to see additional engines please create a new [issue](https://github.com/SEPIA-Framework/sepia-stt-server/issues). Pull requests are welcome ;-)

## Quick-Start

The easiest way to get started is to use a Docker container for your platform:
- x86 64Bit Systeme (Desktop PCs, Linux server etc.): `docker pull sepia/stt-server:v2_amd64_beta`
- ARM 32Bit (Raspberry Pi 4 32Bit OS): `docker pull sepia/stt-server:v2_armv7l_beta`
- ARM 64Bit (RPi 4 64Bit, Jetson Nano(?)): `docker pull sepia/stt-server:v2_aarch64_beta`

After the download is complete simply start the container, for example via:  
```
sudo docker run --name=sepia-stt -p 20741:20741 -it sepia/stt-server:[platform-tag]
```

To test the server visit: `http://localhost:20741` if you are on the same machine or `http://[server-IP]:20741` if you are in the same network (NOTE: custom recordings via microphone will only work using localhost or a HTTPS URL!).

## Server Settings

Most of the settings can be handled easily via the [server.conf settings file](src/server.conf). Please check out the file to see whats possible.

ENV variables:
- `SEPIA_STT_SETTINGS`: Overwrites default path to settings file

Commandline options:
- Use `python -m launch -h` to see all commandline options
- Use `python -m launch -s [path-to-file]` to use custom settings

NOTE: Commandline options always overrule the settings file but in most scenarios it makes sense to simply create a new settings file and use the `-s` flag.

## ASR Engine Settings

As soon as the server is running you can check the current setup via the HTTP REST interface: `http://localhost:20741//settings` or the test page (see quick-start above).  
  
Individual settings for the active engine can be changed on-the-fly during the WebSocket 'welcome' event. See the [API docs](API.md) file for more info or check out the 'Engine Settings' section of the test page.

## How to use with SEPIA Client

The [SEPIA Client](https://github.com/SEPIA-Framework/sepia-html-client-app) will support the new STT server (v2) out-of-the-box from version 0.24.0 on. 
Simply open the client's settings, look for 'ASR engine (STT)' and select `SEPIA`. The server address will be set automatically relative to your SEPIA Server host. 
If your SEPIA server proxy has not been updated yet to forward requests to the SEPIA STT-Server you can enter the direct URL via the STT settings page, e.g.: `http://localhost:20741` or `http://localhost:20726/sepia/stt`.
The settings will allow you to select a specific ASR model for each client language as well (if you don't want to use the language defaults set by your STT server config).  
  
NOTE: Keep in mind that the client's microphone will [only work in a secure environment](https://github.com/SEPIA-Framework/sepia-docs/wiki/SSL-for-your-Server) (that is localhost or HTTPS) 
and thus the link to your server must be secure as well (e.g. use a real domain and SSL certificate, self-signed SSL or a proxy running on localhost).

## Develop your own client

See the separate [API docs](API.md) file or check out the [Javascript client class](src/www/audio-modules/shared/sepia-stt-socket-client.js) and the [test page](src/www/test.html) source-code.  
  
Demo clients:
- Server test page(s): `http://localhost:20741` (with microphone) or `http://[server-IP]:20741` (no microphone due to "insecure" origin)
- [SEPIA Client app](https://sepia-framework.github.io/app/) (v0.24+, simply skip the login, go to settings and enter your server URL)

## Adapt ASR models

Open-source ASR has improved a lot in the last years but sometimes it makes sense to adapt the models to your own, specific use-case and vocabulary to improve accuracy.
The language model adaptation process will be integrated into the server in the near future. Until then please check out the following links:

- Language model adaptation made easy with [kaldi-adapt-lm](https://github.com/fquirin/kaldi-adapt-lm)
