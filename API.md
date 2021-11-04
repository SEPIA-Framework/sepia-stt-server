# SEPIA Speech-To-Text Server API

This document describes the API to communicated with SEPIA Speech-To-Text (STT) Server.

[UNDER CONSTRUCTION: Please create an issue to push me and update this :-p]  
  
In the meantime please follow the discussion here: https://github.com/SEPIA-Framework/sepia-docs/discussions/112  
or check out the [Javascript client](src/www/audio-modules/shared/sepia-stt-socket-client.js) and [test-page](src/www/test-page.html) for a code examples.

## General information

Communication with the server is handled via WebSocket messages in JSON format. Each message has a specific 'type' that defines it's purpose (e.g. handle configuration, send audio chunks etc.).
The general flow of events is as follows:

* The client opens a WebSocket connection using the URL: `ws://[server-ip]:[port]/socket` (or wss:// if you use custom SSL) and listens for the `onopen` event.
* If the `onopen` event arrives the client sends a 'welcome' message in JSON format that contains the authentication data and desired ASR configuration. It then checks `onmessage` for a response of the same type and `onerror` for ... errors.
* If the welcome message was confirmed the client starts sending chunks of audio (raw audio buffer) to the server. This can be a typed-array, blob or binary data, depending on your client language.
* The server starts the transcription process and will send "partial" and "final" results (type 'result') in JSON format. The client receives the results via the `onmessage` handler.
* Depending on the settings (continuous=true/false) or other conditions either server or client will end the process and close the connection. The client listens for `onclose` and `onerror` events.
* The client can close the connection anytime by sending a JSON message of type 'audioend' indicating that it will not send any more audio chunks. The server will then try to finalize the running process and send a final result.

## Ping the server and get settings

To check if the server is actually online you can send a simple HTTP GET request to the 'ping' endpoint: `[server-ip]:[port]/ping`.  
The answer will be something like this: `{"result":"success","server":"SEPIA STT Server","version":"0.9.5"}`.  
  
There is another GET endpoint called `/settings` that will give you some more details, e.g.:
```
{
	"result": "success",
	"settings": {
		"version": "0.9.5",
		"engine": "vosk",
		"models": ["vosk-model-small-de", "vosk-model-small-en-us"],
		"languages": ["de-DE", "en-US"],
		"features": ["partial_results", "alternatives", "words_ts", "phrase_list", "speaker_detection"]
	}
}
```

## Client connection and 'welcome' message

The 'welcome' message should be sent after the WebSocket `onopen` event is received. It authenticates the user and tells the server what model and parameters should be used to do speech recognition.  
  
The 'data' parameter (here we name it 'optionsData') defines things like the samplerate (almost always 16000), if the ASR process stops after a "final" result (continuous=true/false), what language to use and what ASR model etc..  
If the 'model' parameter is not given the server will choose the first available model for the given 'language'. NOTE: 'model' can overrule 'language' if there is a mismatch.
```
optionsData = {
	"samplerate": 16000,
	"language": "en-US",
	"model": "vosk-model-small-en-us",
	"optimizeFinalResult": true,
	"alternatives": 1,
	"continuous": false,
	...
}
```

Some engines can have additional parameters like "phrases" for Vosk. You use the included demos to play with the available options.  
  
Send the event:
```
websocket.send({
	"type": "welcome",
	"data": optionsData,
	"client_id": clientId,
	"access_token": accessToken,
	"msg_id": messageId
})
```

* `type` - Socket message type, in this case 'welcome'.
* `data` - Configuration data for the ASR process, see 'optionsData' above.
* `client_id` and `access_token` - Defined inside [server.conf](src/server.conf), e.g. 'user001' and 'ecd71870d19...' or by default 'any' and 'test1234' (`common_auth_token`).
* `msg_id` - Auto-index number you can assign to any message to track responses (e.g.: 1, 2, ...).

## Welcome response

If the welcome event was successful you will get a response like this (example for Vosk, msg_id=1):
```
{
	"type": "welcome",
	"msg_id": 1,
	"code": 200,
	"info": {
		"version": "0.9.5",
		"engine": "vosk",
		"models": ["vosk-model-small-de", "vosk-model-small-en-us"],
		"languages": ["de-DE", "en-US"],
		"features": ["partial_results", "alternatives", "words_ts", "phrase_list", "speaker_detection"],
		"options": {
			"language": "en-US",
			"model": "vosk-model-small-en-us",
			"samplerate": 16000,
			"optimizeFinalResult": true,
			"alternatives": 1,
			"continuous": false,
			"words": false,
			"speaker": false,
			"phrases": []
		}
	}
}
```

The object will contain the actual, active settings in response to your welcome-request and in addition some info like the available models, languages, features of the server etc..  
If something went wrong like a failed authentication you will get an error message in return.

## Sending chunks of audio

TBD

## Transcription Results

TBD

## Ping-pong message to keep connection alive

TBD
