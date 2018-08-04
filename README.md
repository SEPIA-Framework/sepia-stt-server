# SEPIA Speech-To-Text Server
  
[UNDER CONSTRUCTION]  
  
This server supports streaming audio over a WebSocket connection with integration of an open-source ASR decoder like the Kaldi speech recognition toolkit. It can handle full-duplex messaging during the decoding process for intermediate results. The REST interface of the server allows to switch the ASR model on-the-fly.

## Features
* Websocket server (Python Tornado) that can receive (and send) audio streams
* Compatible to [SEPIA Framework client](https://github.com/SEPIA-Framework/sepia-html-client-app)
* Integration of [Zamia Speech](https://github.com/gooofy/zamia-speech) (python-kaldiasr) to use Kalid ASR in Python
* Roughly based on [nexmo-community/audiosocket_framework](https://github.com/nexmo-community/audiosocket_framework)

## Quick-start (tested on Debian9 64bit)

### Install requirements
Make sure you have at least Python 2.7 with pip (e.g.: sudo apt-get install python-pip) installed. You may also need header files for Python and OpenSSL depending on your operating system.
If you are good to go install a few dependencies via pip:  
```bash
pip install tornado webrtcvad numpy
```
Then get the Python Kaldi bindings from [Zamia Speech](https://github.com/gooofy/zamia-speech) (Debian9 64bit example, see link for details):  
```bash
echo "deb http://goofy.zamia.org/repo-ai/debian/stretch/amd64/ ./" >/etc/apt/sources.list.d/zamia-ai.list
wget -qO - http://goofy.zamia.org/repo-ai/debian/stretch/amd64/bofh.asc | sudo apt-key add -
apt-get update
apt-get install python-kaldiasr
```

### Install STT server and run
```bash
git clone https://github.com/SEPIA-Framework/sepia-stt-server.git
cd sepia-stt-server
python sepia_stt_server.py
```
You can check if the server is reachable by calling `http://localhost:20741/ping`

### How to set-up the SEPIA client (this will be easier soon ^^)
Make sure you can reach your STT server via a secure HTTPS connection. If you don't have your own secure web-server you can use [Ngrok](https://ngrok.com/docs) for testing:  
```bash
./ngrok http 20741
```
Then open your SEPIA web-client in Firefox browser (Chrome works too, but is currently set to use Google ASR). 
If you don't run your own version you can use the [official public client](https://sepia-framework.github.io/app/index.html).
Open the browser console and enter:  
`SepiaFW.speechWebSocket.setSocketURI("wss://[MY-NGROK-ADDRESS].nkrok.io/socket")`  
Test the speech recognition via the microphone button :-)

## Configuration
The application reads its configuration on start-up from the app.conf file that can be located in several different locations (checked in this order):  
* Home folder of the user: `~/share/sepia_stt_server/app.conf`  
* App folder: `/app/share/sepia_stt_server/app.conf`  
* Base folder of the server app: `./app.conf`  
  
The most important settings are:  
* port: Port of the server, default is 20741. You can use `ngrok http 20741` to tunnel to the SEPIA STT-Server for testing  
* recordings_path: This is where the framework application will store audio files it records, default is "./recordings/"  
* kaldi_model_path: This is where the ASR models for Kaldi are stored, default is "/opt/kaldi/model/kaldi-generic-en-tdnn_sp" as used by Zamia Speech  

### REST Interface
The configuration can be changed while the server is running.  
  
Get the current configuration via HTTP GET to:  
```
curl -X GET http://localhost:20471/settings
```
(Note: Replace localhost by your server or the Ngrok address)  
  
Set a different Kaldi model via HTTP POST, e.g.:  
```
curl -X POST http://localhost:20471/settings \
  -H 'Content-Type: application/json' \
  -d '{"token":"test", "kaldi_model":"/home/user/share/kaldi_models/my-own-model"}'
```
(Note: token=test is a placeholder for future authentication process)  

