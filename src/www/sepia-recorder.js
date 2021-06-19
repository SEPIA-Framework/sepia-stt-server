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
	
	SepiaVoiceRecorder.onResamplerData = function(data){
		console.log("SepiaVoiceRecorder -  onResamplerData", data);
	}
	
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
	
	//recorder processor:
	
	var sepiaWebAudioProcessor;
	var targetSampleRate = 16000;
	var resamplerBufferSize = 512;
	
	async function createRecorder(options){
		if (!options) options = {};
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
						resampleQuality: 4, 	//1 [low] - 10 [best],
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
						recordBufferLimitKb: 500,
						recordBufferLimitMs: options.recordingLimitMs
					}
				}
			}
		};
		SepiaVoiceRecorder.waveEncoder = waveEncoder;
		var waveEncoderIndex;
				
		//put together modules
		var activeModules = [];
		activeModules.push(resampler);
		resamplerIndex = activeModules.length;		
		activeModules.push(waveEncoder);
		waveEncoderIndex = activeModules.length;
		resampler.settings.sendToModules.push(waveEncoderIndex);	//add to resampler
				
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
				waveEncoderSetGate("open");			//start recording
				if (successCallback) successCallback();
			}, noopCallback, errorCallback);
		}else{
			if (errorCallback) errorCallback({name: "ProcessorInitError", message: "SepiaVoiceRecorder doesn't exist yet."});
		}
	}
	SepiaVoiceRecorder.stop = function(stopCallback, noopCallback, errorCallback){
		if (sepiaWebAudioProcessor){
			sepiaWebAudioProcessor.stop(function(info){
				waveEncoderSetGate("close");		//stop recording
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

	//Decode audio file to audio buffer and then to 16bit PCM mono
	SepiaVoiceRecorder.decodeAudioToInt16Mono = function(fileUrl, sampleRate, channels, successCallback, errorCallback){
		if (!sampleRate) sampleRate = 16000;
		if (!channels) channels = 1;
		if (!successCallback) successCallback = console.log;
		if (!errorCallback) errorCallback = console.error;
		SepiaFW.webAudio.readFileAsBuffer(fileUrl, function(encodedArray){
			var offlineAudioContext = new OfflineAudioContext(channels, encodedArray.byteLength, sampleRate);
			offlineAudioContext.decodeAudioData(encodedArray, function(audioBuffer){
				if (channels > 1){
					console.error("SepiaVoiceRecorder.decodeAudioFile - Channels > 1 not supported. Result will only contain data of channel 0.");
				}
				var isFloat32 = true;
				SepiaFW.webAudio.encodeWaveBuffer(audioBuffer.getChannelData(0), sampleRate, channels, isFloat32, 
				function(res){
					try {
						var samplesInt16Mono = new Int16Array(res.wav.buffer);
						successCallback(samplesInt16Mono);
					}catch(err){
						errorCallback(err);
					}
				}, function(err){
					errorCallback(err);
				});
			}, function(err){
				errorCallback(err);
			});
		}, function(err){
			errorCallback(err);
		});
	}
	
	//Add audio data as audio element to page
	SepiaVoiceRecorder.addAudioElementToPage = function(targetEle, audioData, audioType){
		var audioEle = document.createElement("audio");
		audioEle.src = window.URL.createObjectURL((audioData.constructor.name == "Blob")? audioData : (new Blob([audioData], { type: (audioType || "audio/wav") })));
		audioEle.setAttribute("controls", "controls");
		var audioBox = document.createElement("div");
		audioBox.appendChild(audioEle);
		if (!targetEle) targetEle = document.body;
		targetEle.appendChild(audioBox);
	}
	
	//export
	window.SepiaVoiceRecorder = SepiaVoiceRecorder;
})();