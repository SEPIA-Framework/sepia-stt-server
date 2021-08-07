#!/bin/bash
# TODO: make version number variable - add '--no-cache' ?
if [ -n "$(uname -m | grep aarch64)" ]; then
	echo "Building Vosk Docker container for aarch64"
	sudo docker build -t sepia/stt-server:vosk_aarch64 .
elif [ -n "$(uname -m | grep armv7l)" ]; then
	echo "Building Vosk Docker container for armv7l"
	sudo docker build -t sepia/stt-server:vosk_armv7l .
else
	# NOTE: x86 32bit build not supported atm
	echo "Building Vosk Docker container for amd64"
	sudo docker build -t sepia/stt-server:vosk_amd64 .
fi
