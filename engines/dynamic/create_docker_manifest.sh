#!/bin/bash
version=latest
if [ -n "$1" ]; then
	version=$1
else
	echo "Please specify the version to use for 'latest' release, e.g. 'v1.0.0'"
	exit
fi
sudo docker manifest create sepia/stt-server:latest \
--amend "sepia/stt-server:dynamic_${version}_aarch64" \
--amend "sepia/stt-server:dynamic_${version}_armv7l" \
--amend "sepia/stt-server:dynamic_${version}_amd64"

sudo docker manifest push sepia/stt-server:latest