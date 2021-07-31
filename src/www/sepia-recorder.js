//Simple voice recorder with fixed parameters using SEPIA Web Audio Lib
(function(){
	var SepiaVoiceRecorder = {};

	//callbacks (defined once because we can have only one instance):

	SepiaVoiceRecorder.onProcessorReady = function(info){
		console.log("SepiaVoiceRecorder -  onProcessorReady", info);
	}
	SepiaVoiceRecorder.onProcessorInitError = function(err){
		console.error("SepiaVoiceRecorder -  onProcessorInitError", err);
	}

	SepiaVoiceRecorder.onAudioStart = function(info){
		console.log("SepiaVoiceRecorder -  onAudioStart");
	}
	SepiaVoiceRecorder.onAudioEnd = function(info){
		console.log("SepiaVoiceRecorder -  onAudioEnd");
	}
	SepiaVoiceRecorder.onProcessorError = function(err){
		console.error("SepiaVoiceRecorder -  onProcessorError", err);
	}

	SepiaVoiceRecorder.onProcessorRelease = function(info){
		console.log("SepiaVoiceRecorder -  onProcessorRelease");
	}

	SepiaVoiceRecorder.onDebugLog = function(msg){
		console.log("debugLog", msg);
	}
	
	//Resampler events
	SepiaVoiceRecorder.onResamplerData = function(data){
		console.log("SepiaVoiceRecorder -  onResamplerData", data);
	}
	
	//Wave encoder events
	SepiaVoiceRecorder.onWaveEncoderStateChange = function(state){
		console.log("SepiaVoiceRecorder -  onWaveEncoderStateChange", state);
	}
	SepiaVoiceRecorder.onWaveEncoderAudioData = function(waveData){
		console.log("SepiaVoiceRecorder -  onWaveEncoderAudioData", waveData);
		//SepiaVoiceRecorder.addAudioElementToPage(targetEle, waveData, "audio/wav");
	}
	function onWaveEncoderData(data){
		if (data.output && data.output.wav){
			SepiaVoiceRecorder.onWaveEncoderAudioData(data.output.wav);
			
		}else if (data.output && data.output.buffer){
			//plotData(data.output.buffer);
			//console.log("waveEncoder", "buffer output length: " + data.output.buffer.length);
		}
		if (data.gate){
			SepiaVoiceRecorder.onWaveEncoderStateChange(data.gate);
			if (data.gate.isOpen === true){
				waveEncoderIsBuffering = true;
				
			}else if (data.gate.isOpen === false){
				if (waveEncoderIsBuffering){
					waveEncoderGetWave();		//we use this by default?
				}
				waveEncoderIsBuffering = false;
			}
		}
	}
	var waveEncoderIsBuffering = false;
	
	//Voice-Activity-Detection events
	SepiaVoiceRecorder.onVadStateChange = function(state, code){
		console.log("SepiaVoiceRecorder -  onVadStateChange", state, code);
	}
	function onVadData(data){
		//console.log("onVadData", data);	//DEBUG
		if (data.voiceActivity != undefined){}
		if (data.voiceEnergy != undefined){}
		if (data.vadSequenceCode != undefined){
			//console.log("VAD sequence event: " + data.vadSequenceMsg);		//DEBUG
			if (data.vadSequenceCode == 1){
				SepiaVoiceRecorder.onVadStateChange("vaup", 1);			//1: voice activity registered
			}else if (data.vadSequenceCode == 2){
				SepiaVoiceRecorder.onVadStateChange("speechstart", 2);	//2: sequence started (continous speech)
			}else if (data.vadSequenceCode == 3){
				SepiaVoiceRecorder.onVadStateChange("vadown", 3);		//3: voice activity gone
			}else if (data.vadSequenceCode == 4){
				SepiaVoiceRecorder.onVadStateChange("speechend", 4);	//4: speech finished max. time
			}else if (data.vadSequenceCode == 5){
				SepiaVoiceRecorder.onVadStateChange("speechend", 5); 	//5: speech finished (sequence end)
				//data.vadSequenceStarted, data.vadSequenceEnded
			}
		}
	}

	//SpeechRecognition events
	SepiaVoiceRecorder.onSpeechRecognitionStateChange = function(ev){
		console.log("SepiaVoiceRecorder -  onSpeechRecognitionStateChange", ev);
	}
	SepiaVoiceRecorder.onSpeechRecognitionEvent = function(data){
		console.log("SepiaVoiceRecorder -  onSpeechRecognitionEvent", data);
	}
	function onSpeechRecognitionData(msg){
		if (!msg) return;
		if (msg.gate){
			//gate closed
			if (msg.gate.isOpen == false && asrModuleGateIsOpen){
				asrModuleGateIsOpen = false;
				//STATE: streamend
				SepiaVoiceRecorder.onSpeechRecognitionStateChange({
					state: "onStreamEnd", 
					bufferOrTimeLimit: msg.gate.bufferOrTimeLimit
				});
			//gate opened
			}else if (msg.gate.isOpen == true && !asrModuleGateIsOpen){
				//STATE: streamstart
				SepiaVoiceRecorder.onSpeechRecognitionStateChange({
					state: "onStreamStart"
				});
				asrModuleGateIsOpen = true;
			}
		}
		if (msg.recognitionEvent){
			SepiaVoiceRecorder.onSpeechRecognitionEvent(msg.recognitionEvent);
		}
		if (msg.connectionEvent){
			//TODO: use? - type: open, ready, closed
		}
		//In debug or test-mode the module might send the recording:
		if (msg.output && msg.output.wav){
			SepiaVoiceRecorder.onWaveEncoderAudioData(msg.output.wav);
		}
	}
	var asrModuleGateIsOpen = false;
	
	//recorder processor:
	
	var sepiaWebAudioProcessor;
	var targetSampleRate = 16000;
	var resamplerBufferSize = 512;
	
	async function createRecorder(options){
		if (!options) options = {};
		else {
			//overwrite shared defaults?
			if (options.targetSampleRate) targetSampleRate = options.targetSampleRate;
			if (options.resamplerBufferSize) resamplerBufferSize = options.resamplerBufferSize;
		}
		var useRecognitionModule = !!options.asr;
		if (typeof options.asr != "object") options.asr = {};
		var useVadModule = !!options.vad;
		if (typeof options.vad != "object") options.vad = {};
		//audio source
		var customSource = undefined;
		if (options.fileUrl){
			//customSourceNode: file audio buffer
			try {
				customSource = await SepiaFW.webAudio.createFileSource(options.fileUrl, {
					targetSampleRate: targetSampleRate
				});
			}catch (err){
				SepiaVoiceRecorder.onProcessorInitError(err);
				return;
			}
		}
		
		var resampler = {
			name: 'speex-resample-switch',
			settings: {
				onmessage: SepiaVoiceRecorder.onResamplerData,
				sendToModules: [],	//index given to processor - 0: source, 1: module 1, ...
				options: {
					processorOptions: {
						targetSampleRate: targetSampleRate,
						resampleQuality: options.resampleQuality || 4, 	//1 [low] - 10 [best],
						bufferSize: resamplerBufferSize,
						passThroughMode: 0,		//0: none, 1: original (float32), 2: 16Bit PCM - NOTE: NOT resampled
						calculateRmsVolume: true,
						gain: options.gain || 1.0
					}
				}
			}
		};
		var resamplerIndex;
		
		var waveEncoder = {
			name: 'wave-encoder',
			type: 'worker',
			handle: {},		//will be updated on init. with ref. to node.
			settings: {
				onmessage: onWaveEncoderData,
				options: {
					setup: {
						inputSampleRate: targetSampleRate,
						inputSampleSize: resamplerBufferSize,
						lookbackBufferMs: 0,
						recordBufferLimitKb: 500,		//default: 5MB (overwritten by ms limit), good value e.g. 600
						recordBufferLimitMs: options.recordingLimitMs,
						doDebug: false
					}
				}
			}
		};
		var waveEncoderIndex;
		
		var defaultVadBuffer = 480*2;	//480 is the 30ms window for WebRTC VAD 16k - its a bit "special"
		var vadWorker = {
			name: 'webrtc-vad-worker', 	//More experimental version: 'sepia-vad-worker'
			type: 'worker',
			settings: {
				onmessage: onVadData,
				options: {
					setup: {
						inputSampleRate: targetSampleRate,
						inputSampleSize: resamplerBufferSize,
						bufferSize: options.vad.bufferSize || defaultVadBuffer, //restrictions apply ^^
						vadMode: options.vad.mode || 3,
						sequence: {
							silenceActivationTime: 450, //250,
							maxSequenceTime: options.vad.maxSequenceTime || 10000,
							minSequenceTime: options.vad.minSequenceTime || 600
						}
					}
				}
			}
		};
		var vadWorkerIndex;

		var sttServerModule = {
			name: 'stt-socket',
			type: 'worker',
			handle: {},		//will be updated on init. with ref. to node.
			settings: {
				onmessage: onSpeechRecognitionData,
				options: {
					setup: {
						//rec. options
						inputSampleRate: targetSampleRate,
						inputSampleSize: resamplerBufferSize,
						lookbackBufferMs: 0,
						recordBufferLimitKb: 500,			//default: 5MB (overwritten by ms limit), good value e.g. 600
						recordBufferLimitMs: options.recordingLimitMs,	//NOTE: will not apply in 'continous' mode (but buffer will not grow larger)
						//ASR server options
						serverUrl: options.asr.serverUrl,	//NOTE: if set to 'debug' it will trigger "dry run" (wav file + pseudo res.)
						clientId: options.asr.clientId,
						accessToken: options.asr.accessToken,
						//ASR engine common options
						messageFormat: options.asr.messageFormat || "webSpeechApi",		//use events in 'webSpeechApi' compatible format
						language: options.asr.language || "",
						model: options.asr.model || "",
						continuous: (options.asr.continuous != undefined? options.asr.continuous : false),	//one final result only?
						optimizeFinalResult: options.asr.optimizeFinalResult,	//try to optimize result e.g. by converting text to numbers etc.
						//ASR engine specific options (can include commons but will be overwritten with above)
						engineOptions: options.asr.engineOptions || {},			//e.g. ASR model, alternatives, ...
						//other
						returnAudioFile: options.asr.returnAudioFile || false,			//NOTE: can be enabled via "dry run" mode
						doDebug: false
					}
				}
			}
		};
		var sttServerModuleIndex;
				
		//put together modules
		var activeModules = [];
		
		//- resampler is required
		activeModules.push(resampler);
		resamplerIndex = activeModules.length;
		
		//- use VAD?
		if (useVadModule){
			activeModules.push(vadWorker);
			vadWorkerIndex = activeModules.length;
			SepiaVoiceRecorder.vadModule = vadWorker;
			resampler.settings.sendToModules.push(vadWorkerIndex);			//add to resampler
		}
		
		//- use either speech-recognition (ASR) or wave-encoder
		if (useRecognitionModule){
			activeModules.push(sttServerModule);
			sttServerModuleIndex = activeModules.length;
			SepiaVoiceRecorder.sttServerModule = sttServerModule;
			resampler.settings.sendToModules.push(sttServerModuleIndex);	//add to resampler
		}else{
			activeModules.push(waveEncoder);
			waveEncoderIndex = activeModules.length;
			SepiaVoiceRecorder.waveEncoder = waveEncoder;
			resampler.settings.sendToModules.push(waveEncoderIndex);		//add to resampler
		}
				
		//create processor
		sepiaWebAudioProcessor = new SepiaFW.webAudio.Processor({
			onaudiostart: SepiaVoiceRecorder.onAudioStart,
			onaudioend: SepiaVoiceRecorder.onAudioEnd,
			onrelease: SepiaVoiceRecorder.onProcessorRelease,
			onerror: SepiaVoiceRecorder.onProcessorError,
			targetSampleRate: targetSampleRate,
			//targetBufferSize: 512,
			modules: activeModules,
			destinationNode: undefined,		//defaults to: new "blind" destination (mic) or audioContext.destination (stream)
			startSuspended: true,
			debugLog: SepiaVoiceRecorder.onDebugLog,
			customSource: customSource
			
		}, function(msg){
			//Init. ready
			SepiaVoiceRecorder.onProcessorReady(msg);
			
		}, function(err){
			//Init. error
			SepiaVoiceRecorder.onProcessorInitError(err);
		});
	}
	
	//Interface:
	
	SepiaVoiceRecorder.create = function(options){
		if (sepiaWebAudioProcessor){
			SepiaVoiceRecorder.onProcessorInitError({name: "ProcessorInitError", message: "SepiaVoiceRecorder already exists. Release old one before creating new."});
			return;
		}
		if (!options) options = {};
		createRecorder(options);
	}
	
	SepiaVoiceRecorder.isReady = function(){
		return (!!sepiaWebAudioProcessor && sepiaWebAudioProcessor.isInitialized());
	}
	SepiaVoiceRecorder.isActive = function(){
		return (!!sepiaWebAudioProcessor && sepiaWebAudioProcessor.isInitialized() && sepiaWebAudioProcessor.isProcessing());
	}
	SepiaVoiceRecorder.start = function(successCallback, noopCallback, errorCallback){
		if (sepiaWebAudioProcessor){
			sepiaWebAudioProcessor.start(function(){
				waveEncoderSetGate("open");					//start recording
				speechRecognitionModuleSetGate("open");		//start recognition
				if (successCallback) successCallback();
			}, noopCallback, errorCallback);
		}else{
			if (errorCallback) errorCallback({name: "ProcessorInitError", message: "SepiaVoiceRecorder doesn't exist yet."});
		}
	}
	SepiaVoiceRecorder.stop = function(stopCallback, noopCallback, errorCallback){
		if (sepiaWebAudioProcessor){
			sepiaWebAudioProcessor.stop(function(info){
				waveEncoderSetGate("close");				//stop recording
				speechRecognitionModuleSetGate("close");	//stop recognition
				if (stopCallback) stopCallback(info);
			}, noopCallback, errorCallback);
		}else{
			if (noopCallback) noopCallback();
		}
	}
	SepiaVoiceRecorder.release = function(releaseCallback, noopCallback, errorCallback){
		if (sepiaWebAudioProcessor){
			sepiaWebAudioProcessor.release(function(){
				sepiaWebAudioProcessor = undefined;
				if (releaseCallback) releaseCallback();
			}, function(){
				sepiaWebAudioProcessor = undefined;
				if (noopCallback) noopCallback();
			}, function(err){
				sepiaWebAudioProcessor = undefined;
				if (errorCallback) errorCallback(err);
			});
		}else{
			if (noopCallback) noopCallback();
		}
	}
	//stop and release if possible or confirm right away
	SepiaVoiceRecorder.stopIfActive = function(callback){
		if (SepiaVoiceRecorder.isActive()){
			SepiaVoiceRecorder.stop(callback, callback, undefined);
		}else{
			if (callback) callback();
		}
	}
	SepiaVoiceRecorder.stopAndReleaseIfActive = function(callback){
		SepiaVoiceRecorder.stopIfActive(function(){
			if (SepiaVoiceRecorder.isReady()){
				SepiaVoiceRecorder.release(callback, callback, undefined);
			}else{
				sepiaWebAudioProcessor = undefined;
				if (callback) callback();
			}	
		});
	}
	
	//Extras:
	
	function waveEncoderSetGate(state){
		if (sepiaWebAudioProcessor && SepiaVoiceRecorder.waveEncoder){
			SepiaVoiceRecorder.waveEncoder.handle.sendToModule({gate: state});	//"open", "close"
		}
	}
	function waveEncoderGetWave(){
		if (sepiaWebAudioProcessor && SepiaVoiceRecorder.waveEncoder){
			SepiaVoiceRecorder.waveEncoder.handle.sendToModule({request: {get: "wave"}});
		}
	}
	function speechRecognitionModuleSetGate(state){
		if (sepiaWebAudioProcessor && SepiaVoiceRecorder.sttServerModule){
			SepiaVoiceRecorder.sttServerModule.handle.sendToModule({gate: state});	//"open", "close"
		}
	}

	//Decode audio file to audio buffer and then to 16bit PCM mono
	SepiaVoiceRecorder.decodeAudioFileToInt16Mono = function(fileUrl, sampleRate, channels, successCallback, errorCallback){
		if (!sampleRate) sampleRate = 16000;
		if (channels && channels > 1){
			console.error("SepiaVoiceRecorder.decodeAudioFileToInt16Mono - Channels > 1 not supported. Result will only contain data of channel 0.");
		}
		if (!successCallback) successCallback = console.log;
		if (!errorCallback) errorCallback = console.error;
		SepiaFW.webAudio.decodeAudioFileToInt16Mono(fileUrl, sampleRate, successCallback, errorCallback);
	}
	
	//Add audio data as audio element to page
	SepiaVoiceRecorder.addAudioElementToPage = function(targetEle, audioData, audioType){
		return SepiaFW.webAudio.addAudioElementToPage(targetEle, audioData, audioType);
	}
	
	//export
	window.SepiaVoiceRecorder = SepiaVoiceRecorder;
})();