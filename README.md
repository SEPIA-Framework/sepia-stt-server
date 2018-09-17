# SEPIA Speech-To-Text Server
  
[BETA - UNDER CONSTRUCTION]  
  
This server supports streaming audio over a WebSocket connection with integration of an open-source ASR decoder like the Kaldi speech recognition toolkit. It can handle full-duplex messaging during the decoding process for intermediate results. The REST interface of the server allows to switch the ASR model on-the-fly.

## Features
* Websocket server (Python Tornado) that can receive (and send) audio streams
* Compatible to [SEPIA Framework client](https://github.com/SEPIA-Framework/sepia-html-client-app)
* Integration of [Zamia Speech](https://github.com/gooofy/zamia-speech) (python-kaldiasr) to use Kalid ASR in Python
* Roughly based on [nexmo-community/audiosocket_framework](https://github.com/nexmo-community/audiosocket_framework)

## Using the Docker image

Make sure you have Docker installed then pull the image via the command-line:  
```bash
docker pull sepia/stt-server:beta1 
```
Once the image has finished downloading (~1GB, extracted ~3.3GB) you can run it using:  
```bash
docker run --rm --name=sepia_stt -d -p 9000:8080 sepia/stt-server:beta1
```
This will start the STT server (with internal proxy running on port 8080 with path '/stt') and expose it to port 9000 (choose whatever you need here).  
To test if the server is working you can call the settings interface with:  
```bash
curl http://localhost:9000/stt/settings && echo
```
You should see a JSON response indicating the ASR model and server version.  
To stop the server use:  
```bash
docker stop sepia_stt
```
To change the server settings, add your own ASR models, do language model customization or to capture your recordings for later you can use the internal 'share' folder like this:  
```bash
wget -O share-folder.zip https://github.com/SEPIA-Framework/sepia-stt-server/blob/master/share-folder.zip?raw=true
unzip share-folder.zip -d /home/[my user]/sepia-stt-share/
docker run --rm --name=sepia_stt -d -p 9000:8080 -v /home/[my user]/sepia-stt-share:/apps/share sepia/stt-server:beta1
```
where `/home/[my user]/sepia-stt-share` is just an example for any folder you would like to use (e.g. in Windows it could be C:/sepia/stt-share). 
When setup like this the server will load it's configuration from the app.conf in your shared folder.

## Custom installation (tested on Debian9 64bit)

### Requirements
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
Download one (or more) of their great ASR models too! I recommend 'kaldi-generic-en-tdnn_sp'.

### Install STT server and run
```bash
git clone https://github.com/SEPIA-Framework/sepia-stt-server.git
cd sepia-stt-server
python sepia_stt_server.py
```
You can check if the server is reachable by calling `http://localhost:20741/ping`

### Configuration
The application reads its configuration on start-up from the app.conf file that can be located in several different locations (checked in this order):  
* Home folder of the user: `~/share/sepia_stt_server/app.conf`  
* App folder: `/apps/share/sepia_stt_server/app.conf`  
* Base folder of the server app: `./app.conf`  
  
The most important settings are:  
* port: Port of the server, default is 20741. You can use `ngrok http 20741` to tunnel to the SEPIA STT-Server for testing  
* recordings_path: This is where the framework application will store audio files it records, default is "./recordings/"  
* kaldi_model_path: This is where the ASR models for Kaldi are stored, default is "/opt/kaldi/model/kaldi-generic-en-tdnn_sp" as used by Zamia Speech  

## How to set-up the SEPIA client
Make sure you can reach your STT server via a secure HTTPS connection. If you don't have your own secure web-server you can use [Ngrok](https://ngrok.com/docs) for testing, e.g.:  
```bash
./ngrok http 20741
```
Choose the right port depending on your app.conf and your Docker run command (in case you are using the Docker image). 
Then open your SEPIA web-client (v0.12.1+). If you don't run your own version you can use the [official public client](https://sepia-framework.github.io/app/index.html).
Go to the menu and look for 'ASR engine' and 'ASR server' (page 2). If your browser supports the 'MediaDevices' interface you will be able to select 'Custom (WebSocket)' here.
Finally set your 'ASR server', e.g.:  
`wss://[MY-NGROK-ADDRESS].nkrok.io/socket` (if you run the server directly using Ngrok) or  
`wss://[MY-NGROK-ADDRESS].nkrok.io/stt/socket` (if you're using the Docker image).  
Test the speech recognition via the microphone button :-)

## REST Interface
The configuration can be changed while the server is running.  
  
Get the current configuration via HTTP GET to:  
```
curl -X GET http://localhost:20471/settings
```
(Note: Replace localhost by your server or localhost:port with the Ngrok address. When you are using the Docker image your server is using a proxy; add: '/stt/settings' to the path like in the client setup).  
  
Set a different Kaldi model via HTTP POST, e.g.:  
```
curl -X POST http://localhost:20471/settings \
  -H 'Content-Type: application/json' \
  -d '{"token":"test", "kaldi_model":"/home/user/share/kaldi_models/my-own-model"}'
```
(Note: token=test is a placeholder for future authentication process)  

