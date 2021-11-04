# SEPIA Speech-To-Text Server

### Requirements

Python 3.7 is recommended.  
Please see 'requirements.txt' for more details or check out the **Dockerfile** inside the engines folder (`../engines/`).  
Basic setup (the Vosk part might not work on all machines out-of-the-box):

```
pip install fastapi
pip install uvicorn[standard]
pip install aiofiles
pip install vosk
```

### Download the Server and ASR Models

Example to download the code into `$HOME/sepia-stt`:
```
cd $HOME
mkdir -p sepia-stt/server && mkdir -p sepia-stt/models
git clone --single-branch --depth 1 -b master https://github.com/SEPIA-Framework/sepia-stt-server.git
mv sepia-stt-server/src sepia-stt/server
```

Before you run the server please download the release models, extract the ZIP files and copy them into the models folder (removing the version tag). Example:
```
cd $HOME/sepia-stt
mkdir -p downloads && cd downloads
wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-en-us-0.15.zip
wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-de-0.15.zip
wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-spk-0.4.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 ../models/vosk-model-small-en-us
unzip vosk-model-small-de-0.15.zip
mv vosk-model-small-de-0.15 ../models/vosk-model-small-de
unzip vosk-model-spk-0.4.zip
mv vosk-model-spk-0.4 ../models/vosk-model-spk
```

You can use other [Vosk ASR models](https://alphacephei.com/vosk/models) or [build your own](https://github.com/SEPIA-Framework/sepia-stt-server#using-customized-asr-models).  
To add new models please modify your `server.conf` by adding a path and language line to the "[asr_models]" section, e.g.: `path3=my/new-model-es` and `lang3=es-ES`.

### Run

If you've followed the instructions above go to `$HOME/sepia-stt/server` ('src' folder of the repo) and use:
```
python -m launch
```

To see all commandline options run `python -m launch --help`.

### Test

Open: `http://localhost:20741/www/index.html`
