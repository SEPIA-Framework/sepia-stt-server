#!/bin/bash
version=latest
if [ -n "$1" ]; then
	version=$1
else
	echo "Please specify the image version, e.g. 'v1.0.0'"
	exit
fi
if [ -n "$(uname -m | grep aarch64)" ]; then
	echo "Building 'dynamic' Docker container for ${version}_aarch64"
	sudo docker build --no-cache -t sepia/stt-server:"dynamic_${version}_aarch64" .
elif [ -n "$(uname -m | grep armv7l)" ]; then
	echo "Building 'dynamic' Docker container for ${version}_armv7l"
	sudo docker build --no-cache -t sepia/stt-server:"dynamic_${version}_armv7l" .
else
	# NOTE: x86 32bit build not supported atm
	echo "Building 'dynamic' Docker container for ${version}_amd64"
	sudo docker build --no-cache -t sepia/stt-server:"dynamic_${version}_amd64" .
fi
