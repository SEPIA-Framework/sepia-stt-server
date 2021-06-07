# SEPIA Speech-To-Text Server

### Requirements

```
pip install fastapi
pip install uvicorn[standard]
pip install aiofiles
```

### Run

```
uvicorn server:app --host 0.0.0.0 --port 20741 --log-level info --reload
```
