# SEPIA Speech-To-Text Server

### Requirements

Python 3.7 is recommended.  
Please see 'requirements.txt' for more details or check out the 'Dockerfile' (engines folder).  
Basic setup (the Vosk part might not work on all machines):

```
pip install fastapi
pip install uvicorn[standard]
pip install aiofiles
pip install vosk
```

### Run

```
python -m launch
```

To see all commandline options run `python -m launch --help`.

### Test

Open: `http://localhost:20741/www/index.html`
