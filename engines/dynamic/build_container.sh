#!/bin/bash
version=latest
if [ -n "$1" ]; then
	version=$1
fi
if [ -n "$(uname -m | grep aarch64)" ]; then
	echo "Building 'dynamic' Docker container for $version_aarch64"
	sudo docker build --no-cache -t sepia/stt-server:"dynamic_$version_aarch64" .
elif [ -n "$(uname -m | grep armv7l)" ]; then
	echo "Building 'dynamic' Docker container for $version_armv7l"
	sudo docker build --no-cache -t sepia/stt-server:"dynamic_$version_armv7l" .
else
	# NOTE: x86 32bit build not supported atm
	echo "Building 'dynamic' Docker container for $version_amd64"
	sudo docker build --no-cache -t sepia/stt-server:"dynamic_$version_amd64" .
fi
