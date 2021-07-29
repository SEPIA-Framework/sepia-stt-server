//imports
importScripts('./shared/ring-buffer.min.js');

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
				console.error("WaveEncoderWorker - Unknown control message:", e.data);
				break;
		}
	}
	//custom interface
	if (e.data.gate != undefined){
		if (doDebug) console.error("WaveEncoderWorker - DEBUG - Message", e.data);			//DEBUG
		gateControl(e.data.gate && e.data.gate == "open", e.data.gateOptions);
	}
	if (e.data.request){
		if (doDebug) console.error("WaveEncoderWorker - DEBUG - Message", e.data);			//DEBUG
		if (e.data.request.get){
			switch (e.data.request.get){
				case "buffer":
					getBuffer(e.data.request.start, e.data.request.end);
					break;
				case "wave":
					getWave(e.data.request.start, e.data.request.end);
					break;
				default:
					console.log("WaveEncoderWorker - Unknown request message:", e.data);
					break;
			}
		}else if (e.data.request.clear){
			switch (e.data.request.clear){
				case "buffer":
					//TODO: clear buffer and release lookback lock
					break;
				default:
					console.log("WaveEncoderWorker - Unknown request message:", e.data);
					break;
			}
		}else{
			console.log("WaveEncoderWorker - Unknown request message:", e.data);
		}
	}else if (e.data.encode && e.data.encode.data){
		encodeInterface(e.data.encode);
	}
};

let workerId = "wave-encoder-worker-" + Math.round(Math.random() * 1000000) + "-" + Date.now();
let doDebug = false;
let wasConstructorCalled = false;

let inputSampleRate;
let inputSampleSize;
let channelCount;
let isFloat32Input;		//default false
let encoderBitDepth = 16;
let _bytesPerSample = encoderBitDepth/8;

let lookbackBufferMs;
let lookbackBufferNeedsReset;
let _lookbackBufferSize;
let _lookbackRingBuffer;
let recordedBuffers;
let recordBufferMaxN;

let gateIsOpen = false;
let _gateOpenTS = 0;
let _gateCloseTS = 0;

let _isFirstValidProcess = true;

function init(){
	recordedBuffers = null;
	_lookbackRingBuffer = null;
	lookbackBufferNeedsReset = false;
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
	_isFirstValidProcess = true;
	gateIsOpen = false;
	_gateOpenTS = 0;
	_gateCloseTS = 0;
}

//Requests

function getBuffer(start, end){
	//TODO: use start, end
	var res = buildBuffer(start, end);
	postMessage({
		moduleResponse: true,		//on-demand response type
		output: {
			buffer: res.buffer
		}
	});
}
function getWave(start, end){
	//TODO: use start, end
	var res = buildBuffer(start, end);
	var view = encodeWAV(res.buffer, inputSampleRate, channelCount, res.isFloat32);

	postMessage({
		moduleResponse: true,
		output: {
			wav: view,
			sampleRate: inputSampleRate,
			totalSamples: ((view.byteLength - 44)/_bytesPerSample),
			channels: channelCount
		}
	});
}
function encodeInterface(e){
	var format = e.format;
	if (format == "wave"){
		var samples = e.data.samples[0];		//TODO: MONO only or interleaved stereo in channel 1
		var view = encodeWAV(samples, e.data.sampleRate, e.data.channels, e.data.isFloat32);
		postMessage({
			moduleResponse: true,
			encoderResult: {
				wav: view,
				sampleRate: inputSampleRate,
				channels: channelCount
			}
		});
	}else{
		postMessage({
			moduleResponse: true,
			encoderResult: {}, 
			error: "format not supported"
		});
	}
}

function gateControl(open, gateOptions){
	if (!gateOptions) gateOptions = {}; 		//TODO: use e.g. for (lookbackBufferNeedsReset = false)
	var msg = {
		moduleEvent: true,		//use 'moduleEvent' to distinguish from normal processing result
		gate: {}
	};
	if (open){
		//TODO: we should reset some stuff here, for now:
		if (!gateOptions.appendAudio){
			recordedBuffers = [];		//NOTE: by default we reset the buffer
		}else if (recordBufferMaxN && recordedBuffers.length >= recordBufferMaxN){
			recordedBuffers = [];
		}
		_gateOpenTS = Date.now();
		gateIsOpen = true;
		msg.gate.openedAt = _gateOpenTS;
	}else{
		_gateCloseTS = Date.now();
		gateIsOpen = false;
		msg.gate.openedAt = _gateOpenTS;
		msg.gate.closedAt = _gateCloseTS;
		var closedDueToBufferLimit = (recordedBuffers && recordBufferMaxN 
			&& recordedBuffers.length && recordedBuffers.length >= recordBufferMaxN);
		if (closedDueToBufferLimit){
			msg.gate.bufferOrTimeLimit = true;
		}
	}
	msg.gate.isOpen = gateIsOpen;
	postMessage(msg);
}

//Interface

function constructWorker(options){
	if (wasConstructorCalled){
		console.error("WaveEncoderWorker - Constructor was called twice! 2nd call was ignored but this should be fixed!", "-", workerId);	//DEBUG
		return;
	}else{
		wasConstructorCalled = true;
	}
	doDebug = options.setup.doDebug || false;
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
	
	//TODO: add stream output option
	//TODO: lookback audio gets mixed with record sometimes O_o
	
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
			recordLimitMs: Math.ceil((recordBufferMaxN * inputSampleSize * 1000)/inputSampleRate)
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
			//TODO: should we re-init. instead of fail?
		}
		if (gateIsOpen){
			//TODO: this will always be one channel ONLY since the signal is interleaved
			recordedBuffers.push(data.samples[0]);
			//max length
			if (recordBufferMaxN && recordedBuffers.length >= recordBufferMaxN){
				gateControl(false);
				//TODO: after this has triggered the next record sounds distorted???
			}
			if (!lookbackBufferNeedsReset) lookbackBufferNeedsReset = true;
			
		}else if (lookbackBufferMs && !lookbackBufferNeedsReset){
			//do this only until gate was opened .. then wait for buffer export/clear
			_lookbackRingBuffer.push(data.samples);
		}
	}
}

function handleEvent(data){
	//TODO: anything to do?
}

function start(options){
    //TODO: anything to do?
	//NOTE: timing of this signal is not very well defined
}
function stop(options){
    //TODO: anything to do?
	//NOTE: timing of this signal is not very well defined
}
function reset(options){
    //TODO: clean up worker
	init();
}
function release(options){
	//clean up worker and close
	_lookbackRingBuffer = null;
	recordedBuffers = null;
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

function buildBuffer(start, end){
	//TODO: use start, end
	var isFloat32;
	if (recordedBuffers[0]){
		isFloat32 = (recordedBuffers[0] && recordedBuffers[0].constructor.name.indexOf("Float32") >= 0);
		if (doDebug) console.error("WaveEncoderWorker - DEBUG - isFloat32", isFloat32, recordedBuffers[0].constructor.name);
	}
	var lookbackSamples;
	if (_lookbackRingBuffer && _lookbackRingBuffer.framesAvailable){
		if (isFloat32Input){
			lookbackSamples = [new Float32Array(_lookbackRingBuffer.framesAvailable)];
		}else{
			lookbackSamples = [new Int16Array(_lookbackRingBuffer.framesAvailable)];
		}
		_lookbackRingBuffer.pull(lookbackSamples);
	}
	var dataLength = recordedBuffers.length * inputSampleSize + (lookbackSamples? lookbackSamples[0].length : 0);
	//TODO: any chance to allocate 'collectBuffer' in advance and keep it? (max. rec + lookback maybe?)
	var collectBuffer = isFloat32? new Float32Array(dataLength) : new Int16Array(dataLength); 	//TODO: this is usually too big because the last buffer is not full ...
	var n = 0;
	if (lookbackSamples){
		for (let i = 0; i < lookbackSamples[0].length; i++) {
			collectBuffer[n] = lookbackSamples[0][i];
			n++;
		}
	}
	for (let j = 0; j < recordedBuffers.length; j++) {
		for (let i = 0; i < recordedBuffers[j].length; i++) {
			collectBuffer[n] = recordedBuffers[j][i];
			n++;
		}
	}
	if (doDebug) console.error("WaveEncoderWorker - DEBUG - buffer mismatch", n, dataLength);	//TODO: why does this always match?
	//TODO: we clear lookback buffer here ... so we should clear everything
	lookbackBufferNeedsReset = false;
	
	return {
		buffer: collectBuffer,
		isFloat32: isFloat32
	}
}
function clearBuffer(){
	var lookbackSamples;
	if (_lookbackRingBuffer && _lookbackRingBuffer.framesAvailable){
		_lookbackRingBuffer = new RingBuffer(_lookbackBufferSize, channelCount, isFloat32Input? "Float32" : "Int16");
	}
	lookbackBufferNeedsReset = false;
	recordedBuffers = [];
}

function encodeWAV(samples, sampleRate, numChannels, convertFromFloat32){
	if (!samples || !sampleRate || !numChannels){
		console.error("WaveEncoderWorker - encodeWAV - Missing parameters");
		return;
	}
	//Format description: http://soundfile.sapp.org/doc/WaveFormat/
	var bitDepth = encoderBitDepth;
	var bytesPerSample = _bytesPerSample;
	var buffer = new ArrayBuffer(44 + samples.length * bytesPerSample);		//TODO: was (samples.length * 2)
	var view = new DataView(buffer);
	var sampleSize = samples.length;
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
	if (convertFromFloat32){
		wavFloatTo16BitPCM(view, 44, samples);
	}else{
		wavWrite16BitPCM(view, 44, samples);
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
