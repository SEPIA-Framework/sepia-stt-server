# SEPIA Speech-To-Text Server

## Vosk

Below you will find instructions to install the Vosk (only) version of the server.  
For the 'dynamic' version including Conqui-STT please use one of the Docker containers for now.

### Requirements

Python 3.7 is recommended, 3.9 has been tested as well.  
Please see 'requirements.txt' for more details or check out the **Dockerfile** inside the engines folder (`../engines/`).  
  
Install recommended Linux packages (Debian 10|11 example):
```
sudo apt-get install -y python3-pip python3-dev python3-setuptools python3-wheel libffi-dev
```

Basic Pip setup (the Vosk part might not work on all machines out-of-the-box):

```
pip3 install pip --upgrade
pip3 install cffi
pip3 install fastapi
pip3 install uvicorn[standard]
pip3 install aiofiles
pip3 install vosk
```

### Download the Server and ASR Models

Example to download the code into `$HOME/sepia-stt`:
```
cd $HOME
mkdir -p sepia-stt
git clone --single-branch --depth 1 -b master https://github.com/SEPIA-Framework/sepia-stt-server.git
mv sepia-stt-server/src sepia-stt/server
rm -rf sepia-stt-server
```

Before you run the server please download the release models, extract the ZIP files and copy them into the models folder (removing the version tag). Example:
```
cd $HOME/sepia-stt
mkdir -p models
mkdir -p downloads && cd downloads
wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-en-us-0.15.zip
wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-de-0.15.zip
wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-spk-0.4.zip
unzip vosk-model-small-en-us-0.15.zip && mv vosk-model-small-en-us-0.15 ../models/vosk-model-small-en-us
unzip vosk-model-small-de-0.15.zip && mv vosk-model-small-de-0.15 ../models/vosk-model-small-de
unzip vosk-model-spk-0.4.zip && mv vosk-model-spk-0.4 ../models/vosk-model-spk
```

You can use other [Vosk ASR models](https://alphacephei.com/vosk/models) or [build your own](https://github.com/SEPIA-Framework/sepia-stt-server#using-customized-asr-models).  
To add new models please modify your `server.conf` by adding a path and language line to the "[asr_models]" section, e.g.: `path3=vosk-model-small-es` and `lang3=es-ES`.

### Run

If you've followed the instructions above go to `$HOME/sepia-stt/server` ('src' folder of the repo) and use:
```
python -m launch --settings=server-vosk.conf
```

To see all commandline options run `python -m launch --help`.

### Test

Open browser: `http://localhost:20741/www/index.html`  
  
Local test (Vosk): `python test_vosk.py --model [model-path] --wav [test-WAV-path]`
