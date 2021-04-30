#!/bin/bash
# TODO: make version number variable
if [ -n "$(uname -m | grep aarch64)" ]; then
	echo "Building Vosk Docker container 0.3.21 for aarch64"
	sudo docker build -t sepia/stt-server:vosk_0.3.21_aarch64 .
elif [ -n "$(uname -m | grep armv7l)" ]; then
	echo "Building Vosk Docker container 0.3.21 for armv7l"
	sudo docker build -t sepia/stt-server:vosk_0.3.21_armv7l .
else
	# NOTE: x86 32bit build not supported atm
	echo "Building Vosk Docker container 0.3.21 for x86_64"
	sudo docker build -t sepia/stt-server:vosk_0.3.21_x86_64 .
fi
