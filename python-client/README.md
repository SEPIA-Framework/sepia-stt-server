# Python Client for SEPIA Speech-To-Text Server

This is the official Python Client **BETA** for SEPIA Speech-To-Text Server.  
Check-out [example.py](example.py) for a simple demo.

## Quick-Start

- Make sure you have a STT-Server running somewhere (in your network), default: `http://localhost:20741`
- Get the `python-client` folder from this repository
- Install requirements: `pip install requirements_client.txt`
- Make sure your microphone is connected
- Run the demo: `python example.py --server "http://localhost:20741"` or check the options `python example.py -h`
- If the connection to the server works you should see some info messages and a READY event
- Press and hold 'r' to record audio and watch the transcription appear on the screen :-)

## Contribute

If you'd like to build a more advanced Python client and/or like to share your work please feel free to open an new thread in the [discussions section](https://github.com/SEPIA-Framework/sepia-docs/discussions).