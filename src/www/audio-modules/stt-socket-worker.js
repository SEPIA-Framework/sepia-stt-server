//imports
importScripts('./shared/ring-buffer.min.js');
importScripts('./shared/sepia-stt-socket-client.js');

onmessage = function(e) {
    //Audio worker interface
	if (e.data.ctrl){
		switch (e.data.ctrl.action){
			//common interface
			case "construct":
				constructWorker(e.data.ctrl.options);
				break;
			case "process":
				process(e.data.ctrl.data);
				break;
			case "handle":
				handleEvent(e.data.ctrl.data);	//e.g.: this worker sends gate events
				break;
			case "start":
				start(e.data.ctrl.options);
				break;
			case "stop":
				stop(e.data.ctrl.options);
				break;
			case "reset":
				reset(e.data.ctrl.options);
				break;
			case "release":
			case "close":
				release(e.data.ctrl.options);
				break;
			default:
				console.error("SttSocketWorker - Unknown control message:", e.data);
				break;
		}
	}
	//custom interface
	if (e.data.gate != undefined){
		if (doDebug) console.error("SttSocketWorker - DEBUG - Message", e.data);			//DEBUG
		gateControl(e.data.gate && e.data.gate == "open", e.data.gateOptions);
	}
};

let workerId = "stt-socket-worker-" + Math.round(Math.random() * 1000000) + "-" + Date.now();
let doDebug = false;
let enableDryRun = false;		//skip server and generate pseudo result events to debug UI event flow
let returnAudioFile = false;
let wasConstructorCalled = false;

let socketUrl;
let clientId ;
let accessToken;
let sttServer;

let messageFormat;			//e.g.: "webSpeechApi" or "default"

let inputSampleRate;
let inputSampleSize;
let channelCount;
let isFloat32Input;		//default false
let encoderBitDepth = 16;
let _bytesPerSample = encoderBitDepth/8;

let lookbackBufferMs;
let lookbackBufferIsBlocked;
let _lookbackBufferSize;
let _lookbackRingBuffer;
let recordedBuffers;
let _sentBuffers;
let _shiftedBuffers;
let recordBufferMaxN;
let continuous;		//NOTE: this is an engine option but influences full buffer as well

let gateIsOpen = false;
let _gateOpenTS = 0;
let _gateCloseTS = 0;

let _isFirstValidProcess = true;

function init(){
	recordedBuffers = null;
	_lookbackRingBuffer = null;
	lookbackBufferIsBlocked = false;
	if (lookbackBufferMs){
		_lookbackBufferSize = Math.round((lookbackBufferMs/1000) * inputSampleRate);
		if (isFloat32Input){
			_lookbackRingBuffer = new RingBuffer(_lookbackBufferSize, channelCount, "Float32");	//TODO: test for Float32
		}else{
			_lookbackRingBuffer = new RingBuffer(_lookbackBufferSize, channelCount, "Int16");
		}
	}else{
		_lookbackBufferSize = 0;
	}
	recordedBuffers = [];
	_sentBuffers = 0;
	_shiftedBuffers = 0;
	_isFirstValidProcess = true;
	gateIsOpen = false;
	_gateOpenTS = 0;
	_gateCloseTS = 0;
}

//Requests

function gateControl(open, gateOptions, triggeredOnError){
	//console.error("gateControl - open:", open);		//DEBUG
	if (!gateOptions) gateOptions = {}; 		//TODO: use e.g. for ?
	var msg = {
		moduleEvent: true,		//use 'moduleEvent' to distinguish from normal processing result
		gate: {}
	};
	if (open){
		//we always reset the buffer
		recordedBuffers = [];
		_sentBuffers = 0;
		_shiftedBuffers = 0;
		_gateOpenTS = Date.now();
		gateIsOpen = true;
		msg.gate.isOpen = true;
		msg.gate.openedAt = _gateOpenTS;
		//open connection
		if (sttServer){
			sttServer.openConnection();
		}
	}else{
		_gateCloseTS = Date.now();
		gateIsOpen = false;
		msg.gate.isOpen = false;
		msg.gate.openedAt = _gateOpenTS;
		msg.gate.closedAt = _gateCloseTS;
		//---------- DRY-RUN TEST: fake final result ----------
		if (enableDryRun && recordedBuffers.length && recordedBuffers.length > recordBufferMaxN/3){
			setTimeout(function(){
				//final result
				if (messageFormat == "webSpeechApi"){
					sendWebSpeechCompatibleRecognitionResult(true, "End of test message");
				}else{
					sendDefaultRecognitionResult({"type":"result","msg_id":Date.now(),"code":200,"transcript":"End of test message","isFinal":true});
				}
			}, 2000);
		//-------------------------------------------------------
		}else if (sttServer && sttServer.connectionIsOpen && sttServer.isReadyForStream){
			var closedDueToBufferLimit = checkIfBufferLimitWasReached();
			if (closedDueToBufferLimit){
				msg.gate.bufferOrTimeLimit = true;
			}
			//close input and request final result
			requestFinalResult(closedDueToBufferLimit);
		}
		//else we rely on '_gateCloseTS' to finish after last buffer is sent

		//send WAV?
		if (!triggeredOnError && returnAudioFile && recordedBuffers.length){
			setTimeout(function(){
				sendWaveFileArrayBuffer(getWave());
			}, 100);
		}
	}
	postMessage(msg);
}

function getWave(){
	var view;
	var totalLength = 0;
	recordedBuffers.forEach(function(v){
		totalLength += v.byteLength;
	});
	if (totalLength){
		view = new DataView(new ArrayBuffer(totalLength));
		var offset = 0;
		recordedBuffers.forEach(function(v){
			for (let i = 0; i < v.byteLength; i++){
				view.setUint8(offset, v.getUint8(i));
				offset++;
			}
		});
	}
	return view;
}

//Interface

function constructWorker(options){
	if (wasConstructorCalled){
		console.error("SttSocketWorker - Constructor was called twice! 2nd call was ignored but this should be fixed!", "-", workerId);	//DEBUG
		return;
	}else{
		wasConstructorCalled = true;
	}
	doDebug = options.setup.doDebug || false;
	returnAudioFile = options.setup.returnAudioFile || false;

	//recorder
	inputSampleRate = options.setup.inputSampleRate || options.setup.ctxInfo.targetSampleRate || options.setup.ctxInfo.sampleRate;
	inputSampleSize = options.setup.inputSampleSize || 512;
	channelCount = 1;	//options.setup.channelCount || 1;		//TODO: only MONO atm
	lookbackBufferMs = (options.setup.lookbackBufferMs != undefined)? options.setup.lookbackBufferMs : 0;
	isFloat32Input = (options.setup.isFloat32 != undefined)? options.setup.isFloat32 : false;
	
	if (options.setup.recordBufferLimitMs != undefined){
		recordBufferMaxN = (inputSampleRate * options.setup.recordBufferLimitMs/1000) / inputSampleSize;
	}else if (options.setup.recordBufferLimitKb != undefined){
		recordBufferMaxN = (options.setup.recordBufferLimitKb * 1024) / (2 * inputSampleSize);
	}else{
		recordBufferMaxN = 5242880 / (2 * inputSampleSize);	//max 5MB = (5242880[bytes]/(bytesPerSample * sampleSize))
	}
	recordBufferMaxN = Math.ceil(recordBufferMaxN);
	if (recordBufferMaxN < 0) recordBufferMaxN = 0;

	//end on first final result? - NOTE: this works a bit different than WebSpeech "continuous"
	continuous = (options.setup.continuous != undefined)? options.setup.continuous : false;
	//interimResults (unused?)

	//server
	socketUrl = options.setup.socketUrl || options.setup.serverUrl || "http://localhost:20741";
	clientId = options.setup.clientId || "any";
	accessToken = options.setup.accessToken || "test1234";
	messageFormat = options.setup.messageFormat || "default";
	if (socketUrl == "debug"){
		enableDryRun = true;
		returnAudioFile = true;
	}else{
		var engineOptions = options.setup.engineOptions || {};	//all options (common and engine specific)
		//common option shortcuts (overwrites engineOptions - usually supported by all engines):
		engineOptions.samplerate = inputSampleRate;
		engineOptions.continuous = continuous;
		if (options.setup.language) engineOptions.language = options.setup.language;	//e.g.: "de-DE"
		if (options.setup.task) engineOptions.task = options.setup.task;				//e.g.: "conversation"
		if (options.setup.model) engineOptions.model = options.setup.model;				//e.g.: "vosk-model-small-de"
		if (options.setup.optimizeFinalResult != undefined) engineOptions.optimizeFinalResult = options.setup.optimizeFinalResult;
		engineOptions.doDebug = doDebug;
		//special options (e.g. for Vosk):
		/*
		alternatives: 1,
		phrases: [],
		speaker: false,
		words: false
		*/
		//console.error("engineOptions", engineOptions);		//DEBUG
		var serverOptions = {
			onOpen: function(){
				if (doDebug) console.error("SttSocketWorker - DEBUG - CONNECTION OPEN");
				sendConnectionEvent("open");
			},
			onReady: function(activeOptions){
				if (doDebug) console.error("SttSocketWorker - DEBUG - CONNECTION READY", activeOptions);
				sendConnectionEvent("ready", activeOptions);
				//make sure stream starts or continues
				startOrContinueStream();
			},
			onClose: function(){
				if (doDebug) console.error("SttSocketWorker - DEBUG - CONNECTION CLOSED");
				sendConnectionEvent("closed");
			},
			onResult: function(res){
				if (doDebug) console.error("SttSocketWorker - DEBUG - CONNECTION RESULT", res);
				if (messageFormat == "webSpeechApi"){
					sendWebSpeechCompatibleRecognitionResult(res.isFinal, res.transcript);
				}else{
					sendDefaultRecognitionResult(res);
				}
				//if result is final and gate is closed -> close connection
				if (res.isFinal && !gateIsOpen && sttServer && sttServer.connectionIsOpen){
					sttServer.closeConnection();
				}
			},
			onError: function(err){ 
				if (!err) err = {name: "UnknownError", message: "Unknown error"};
				console.error("SttSocketWorker - CONNECTION ERROR", err);
				if (messageFormat == "webSpeechApi"){
					var reason = "unknown";
					if (err.name == "SocketConnectionError"){
						reason = "network";
					}else if (err.name == "Unauthorized"){
						//reason = "not-allowed";	//NOTE: currently mistaken for microphone permission error
						reason = "service-not-allowed";
					}
					sendWebSpeechCompatibleError(reason, err.message || err.name || "");
				}else{
					sendDefaultErrorEvent(err);
				}
				//make sure stream stops
				if (gateIsOpen){
					gateControl(false, {}, true);
				}
			}
		};
		sttServer = new SepiaSttSocketClient(socketUrl, clientId, accessToken, engineOptions, serverOptions);
	}
	
	init();
    	
	postMessage({
		moduleState: 1,
		moduleInfo: {
			moduleId: workerId,
			inputSampleRate: inputSampleRate,
			inputSampleSize: inputSampleSize,
			inputIsFloat32: isFloat32Input,
			channelCount: channelCount,
			lookbackBufferSizeKb: Math.ceil((_lookbackBufferSize * 2)/1024),	//1 sample = 2 bytes
			lookbackLimitMs: lookbackBufferMs,
			recordLimitMs: Math.ceil((recordBufferMaxN * inputSampleSize * 1000)/inputSampleRate),
			sttServerUrl: socketUrl,
			sttServerOptions: (sttServer? sttServer.activeOptions : {})
		}
	});
}

function process(data){
	//expected: data.samples, data.sampleRate, data.targetSampleRate, data.channels, data.type
	//TODO: check process values against constructor values (sampleSize etc.)
	if (data && data.samples){
		if (_isFirstValidProcess){
			//console.error("data info", data);		//DEBUG
			_isFirstValidProcess = false;
			//check: inputSampleRate, inputSampleSize, channelCount, float32
			if (data.sampleRate != inputSampleRate){
				var msg = "Sample-rate mismatch! Should be '" + inputSampleRate + "' is '" + data.sampleRate + "'";
				console.error("Audio Worker sample-rate exception - Msg.: " + msg);
				throw JSON.stringify(new SampleRateException(msg));			//NOTE: this needs to be a string to show up in worker.onerror properly :-/
				return;
			}
			var inputArrayType = data.type || data.samples[0].constructor.name;
			var isFloat32 = (inputArrayType.indexOf("Float32") >= 0);
			if (isFloat32 != isFloat32Input){
				var msg = "Array type mismatch! Input samples are of type '" + inputArrayType + "' but expected: " + (isFloat32Input? "Float32" : "Int16");
				console.error("Audio Worker type exception - Msg.: " + msg);
				throw JSON.stringify(new ArrayTypeException(msg));			//NOTE: this needs to be a string to show up in worker.onerror properly :-/
				return;
			}
		}
		if (gateIsOpen){
			buildPcmChunks(data);
			
		}else if (lookbackBufferMs && !lookbackBufferIsBlocked){
			//do this only until gate was opened .. then wait for buffer export/clear
			_lookbackRingBuffer.push(data.samples);
		}
	}
}

function buildPcmChunks(data){
	//index 0
	if (recordedBuffers.length == 0){
		//0 -- build header
		recordedBuffers.push(getHeaderForWAV(undefined, inputSampleRate, channelCount));
		//1 -- add lookback samples -- TODO: test!
		if (_lookbackRingBuffer && _lookbackRingBuffer.framesAvailable){
			//pull all lookback samples
			var lookbackSamples;
			if (isFloat32Input){
				lookbackSamples = [new Float32Array(_lookbackRingBuffer.framesAvailable)];
			}else{
				lookbackSamples = [new Int16Array(_lookbackRingBuffer.framesAvailable)];
			}
			_lookbackRingBuffer.pull(lookbackSamples);
			//encode and add
			recordedBuffers.push(encodeWAV(undefined, lookbackSamples[0], inputSampleRate, channelCount, isFloat32Input));
		}
		if (doDebug) console.error("SttSocketWorker - DEBUG - Header and Lookback Buffer (optional)", recordedBuffers);
	}
	if (data){
		//TODO: this will always be one channel ONLY since the signal is interleaved
		recordedBuffers.push(encodeWAV(undefined, data.samples[0], inputSampleRate, channelCount, isFloat32Input));
	}
	//---------- DRY-RUN TEST: fake partial result ----------
	if (enableDryRun){
		if (recordedBuffers.length == Math.ceil(recordBufferMaxN/4)){
			if (doDebug) console.error("SttSocketWorker - DEBUG - Reached a quarter of max. time", recordedBuffers.length);
			if (messageFormat == "webSpeechApi"){
				sendWebSpeechCompatibleRecognitionResult(false, "End of ...");
			}else{
				sendDefaultRecognitionResult({"type":"result","msg_id":Date.now(),"code":200,"transcript":"End of ...","isFinal":false});
			}
		}
	//-------------------------------------------------------
	}else if (sttServer && sttServer.connectionIsOpen && sttServer.isReadyForStream){
		//send buffer
		startOrContinueStream();
	}
	//max length
	if (recordBufferMaxN && recordedBuffers.length >= recordBufferMaxN){
		maxLengthReached();
	}
	if (!lookbackBufferIsBlocked) lookbackBufferIsBlocked = true;
}

function startOrContinueStream(){
	//buffer has data and nothing has been sent yet
	if (!_sentBuffers && recordedBuffers.length){
		//send all at once
		var data = new Blob(recordedBuffers);
		_sentBuffers = recordedBuffers.length;
		sendBytes(data);
	
	//buffer has data and some has been sent already
	}else if (_sentBuffers && recordedBuffers.length){
		var normalizedLength = recordedBuffers.length + _shiftedBuffers; //take shifted data into account
		if (_sentBuffers == (normalizedLength - 1)){
			//send last
			var data = recordedBuffers[recordedBuffers.length - 1];
			_sentBuffers++;
			sendBytes(data);

		}else if (_sentBuffers < normalizedLength){
			//send rest at once
			var restN = normalizedLength - _sentBuffers;
			var data = new Blob(recordedBuffers.slice(-1 * restN));
			_sentBuffers += restN;
			sendBytes(data);
		
		}else{
			//ignore
		}
	//no data yet
	}else{
		//ignore
	}
	//no bytes left and stream ended?
	if (_gateCloseTS){
		var closedDueToBufferLimit = checkIfBufferLimitWasReached();
		requestFinalResult(closedDueToBufferLimit);
	}
}
function sendBytes(data){
	sttServer.sendBytes(data);
}

function requestFinalResult(closedDueToBufferLimit){
	//close input and request final result
	var byteLength = 0;
	recordedBuffers.forEach(function(ta){
		byteLength += ta.byteLength;
	});
	sttServer.sendAudioEnd(byteLength, closedDueToBufferLimit);
}

function checkIfBufferLimitWasReached(){
	var reachedBufferLimit = (!continuous && recordedBuffers && recordBufferMaxN 
		&& recordedBuffers.length && recordedBuffers.length >= recordBufferMaxN);
	return reachedBufferLimit;
}

function clearBuffer(){
	if (_lookbackRingBuffer && _lookbackRingBuffer.framesAvailable){
		_lookbackRingBuffer = new RingBuffer(_lookbackBufferSize, channelCount, isFloat32Input? "Float32" : "Int16");
	}
	lookbackBufferIsBlocked = false;
	recordedBuffers = [];
	_sentBuffers = 0;
	_shiftedBuffers = 0;
}

//reached max recording length
function maxLengthReached(){
	if (continuous){
		//drop old buffer
		var shift = (recordedBuffers.length - recordBufferMaxN);
		_shiftedBuffers += shift;
		recordedBuffers.splice(0, shift);
	}else{
		//close
		if (gateIsOpen){
			gateControl(false);
		}
	}
	//TODO: do more ... ?
}

//send result message (partial or final)
function sendWebSpeechCompatibleRecognitionResult(isFinal, transcript){
	if (isFinal && !transcript){
		//this is actually a 'nomatch'/'no-speech' error (no-speech usually fails more gently)
		sendWebSpeechCompatibleError("no-speech", "Final result was empty");
	}else{
		postMessage({
			recognitionEvent: {
				type: "result",
				resultIndex: 0,
				results: [{
					isFinal: isFinal,
					"0": {
						transcript: transcript
					}
				}],
				timeStamp: Date.now()
			},
			eventFormat: "webSpeechApi"
		});
	}
}
function sendDefaultRecognitionResult(event){
	if (event && !event.type) event.type = "result";
	postMessage({
		recognitionEvent: event,
		eventFormat: "default"
	});
}
function sendConnectionEvent(type, data){
	postMessage({
		connectionEvent: {
			type: type,
			data: data
		}
	});
}
//send error message
function sendWebSpeechCompatibleError(errorName, errorMessage){
	var eventName = "error";	//possible as well: "nomatch"
	/*supported errors:
		"network" (1, 2: timeout, 8: busy, 10: rate-limit)
		"audio-capture" (3, happens before worker)
		"unknown" (4, 5)
		"no-speech" (6)
		"nomatch" (7, use eventName)
		"aborted" (?)
		"not-allowed" (9) / "service-not-allowed"
		"bad-grammar" (?)
		"language-not-supported" (12, 13)
	*/
	postMessage({
		recognitionEvent: {
			type: eventName,
			error: errorName,
			message: errorMessage,
			timeStamp: Date.now()
		},
		eventFormat: "webSpeechApi"
	});
}
function sendDefaultErrorEvent(error){
	if (error && !error.type) error.type = "error";
	postMessage({
		recognitionEvent: error,
		eventFormat: "default"
	});
}

//send wave file as array buffer (data view)
function sendWaveFileArrayBuffer(view){
	postMessage({
		moduleResponse: true,	//skip message forwarding?
		output: {
			wav: view,
			sampleRate: inputSampleRate,
			totalSamples: ((view.byteLength - 44)/_bytesPerSample),
			channels: channelCount
		}
	});
}

function handleEvent(data){
	//TODO: anything to do?
}

function start(options){
    //we do nothing but wait for data or gate-open signal
	//NOTE: timing of this signal is not very well defined
}
function stop(options){
	//make sure that gate is closed ... TODO: anything else?
	if (gateIsOpen){
		gateControl(false);
	}
	//NOTE 1: In this case a stopped worker can still send partial or final results.
	//NOTE 2: timing of this signal is not very well defined
}
function reset(options){
	//clean up connection
	if (sttServer && sttServer.connectionIsOpen){
		sttServer.closeConnection();
		//NOTE: we try to reuse this instance
	}
    //clean up worker
	init();
	//TODO: anything else?
}
function release(options){
	//this is expected to happen after final result (or abort) so: clean up connection
	if (sttServer && sttServer.connectionIsOpen){
		sttServer.closeConnection();
	}
	//clean up worker and close
	_lookbackRingBuffer = null;
	recordedBuffers = null;
	_sentBuffers = undefined;
	_shiftedBuffers = undefined;
	gateIsOpen = false;
	_gateOpenTS = 0;
	_gateCloseTS = 0;
	//notify processor that we can terminate now
	postMessage({
		moduleState: 9
	});
}

//--- helpers ---

function SampleRateException(message) {
	this.message = message;
	this.name = "SampleRateException";
}
function ArrayTypeException(message) {
	this.message = message;
	this.name = "ArrayTypeException";
}

//Get header for samples or max size - Format description: http://soundfile.sapp.org/doc/WaveFormat/
function getHeaderForWAV(samples, sampleRate, numChannels){
	var bitDepth = encoderBitDepth;
	var bytesPerSample = _bytesPerSample;
	var view = samples? new DataView(new ArrayBuffer(44 + samples.length * bytesPerSample)) : new DataView(new ArrayBuffer(44));
	//NOTE: this should be "real" size but if we don't know yet take max size - max size includes lookback
	var sampleSize = samples? samples.length : (recordBufferMaxN * inputSampleSize);
	//RIFF identifier
	wavWriteString(view, 0, 'RIFF');
	view.setUint32(4, 36 + (sampleSize * numChannels * bytesPerSample), true);	//TODO: was (samples.length * 2)
	wavWriteString(view, 8, 'WAVE');
	wavWriteString(view, 12, 'fmt ');
	view.setUint32(16, 16, true);	//16 for PCM
	view.setUint16(20, 1, true);	//1 for PCM
	view.setUint16(22, numChannels, true);
	view.setUint32(24, sampleRate, true);
	view.setUint32(28, sampleRate * bytesPerSample * numChannels, true);	//TODO: was (sampleRate * 4)
	view.setUint16(32, numChannels * bytesPerSample, true);
	view.setUint16(34, bitDepth, true);
	wavWriteString(view, 36, 'data');
	view.setUint32(40, (sampleSize * numChannels * bytesPerSample), true);
	return view;
}
function encodeWAV(headerView, samples, sampleRate, numChannels, convertFromFloat32){
	if (!samples || !sampleRate || !numChannels){
		console.error("SttSocketWorker - encodeWAV - Missing parameters");
		return;
	}
	var view;
	var offset;
	if (!headerView){
		view = new DataView(new ArrayBuffer(samples.length * 2));
		offset = 0;
	}else{
		view = headerView;
		offset = 44;
	}
	if (convertFromFloat32){
		wavFloatTo16BitPCM(view, offset, samples);
	}else{
		wavWrite16BitPCM(view, offset, samples);
	}
	return view;
}
function wavFloatTo16BitPCM(view, offset, input) {
	for (let i = 0; i < input.length; i++, offset += 2) {
		let s = Math.max(-1, Math.min(1, input[i]));
		view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
	}
}
function wavWrite16BitPCM(view, offset, input) {
	for (let i = 0; i < input.length; i++, offset += 2) {
		view.setInt16(offset, input[i], true);
	}
}
function wavWriteString(view, offset, string) {
	for (let i = 0; i < string.length; i++) {
		view.setUint8(offset + i, string.charCodeAt(i));
	}
}
