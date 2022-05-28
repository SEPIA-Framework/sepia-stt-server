//Exceptions / Errors

function SampleRateException(message) {
	this.message = message;
	this.name = "SampleRateException";
}
function ArrayTypeException(message) {
	this.message = message;
	this.name = "ArrayTypeException";
}
function SampleSizeException(message){
	this.message = message;
	this.name = "SampleSizeException";
}
function BufferSizeException(message){
	this.message = message;
	this.name = "BufferSizeException";
}
function ChannelCountException(message){
	this.message = message;
	this.name = "ChannelCountException";
}

//Array operations

var ArrayOps = {};

ArrayOps.newCommon1dArray = function(n, startValue){
	if (startValue == undefined) startValue = 0;
	var array = new Array(n);
	for (let i=0; i<n; i++){
		array[i] = startValue;
	}
	return array;
}
ArrayOps.newCommon2dArray = function(n, m, startValue){
	if (startValue == undefined) startValue = 0;
	var array = new Array(n);
	for (let i=0; i<n; i++){
		array[i] = new Array(m);
		for (let j=0; j<m; j++){
			array[i][j] = startValue;
		}
	}
	return array;
}
ArrayOps.pushAndShift = function(array, pushValue){
	//NOTE: this operation does not need to allocate memory compared to shift().push()
	for (let i=0; i<(array.length - 1); i++){
		array[i] = array[i+1];
    }
	array[array.length - 1] = pushValue;
	return array;
};

//Converters

var CommonConverters = {};

CommonConverters.singleSampleFloatTo16BitPCM = function(s){
	s = Math.max(-1, Math.min(1, s));
	return (s < 0 ? s * 0x8000 : s * 0x7FFF);
}
CommonConverters.floatTo16BitPCM = function(output, input){
	for (let i = 0; i < input.length; i++) {
		output[i] = CommonConverters.singleSampleFloatTo16BitPCM(input[i]);
	}
}
CommonConverters.singleSampleInt16ToFloat32BitAudio = function(s){
	//s = Math.max(-32768, Math.min(32767, s));
	return Math.max(-1.0, Math.min(1.0, s/32768));
}
CommonConverters.int16ToFloat32BitAudio = function(output, input){
	for (let i = 0; i < input.length; i++) {
		return CommonConverters.singleSampleInt16ToFloat32BitAudio(input[i]);
	}
}
CommonConverters.uint8ArrayToBase64String = function(uint8Array){
	return btoa(uint8Array.reduce(function(data, byte){ return data + String.fromCharCode(byte); }, ''));
}
