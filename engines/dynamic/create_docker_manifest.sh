#!/bin/bash
version=latest
if [ -n "$1" ]; then
	version=$1
fi
sudo docker manifest create sepia/stt-server:latest \
--amend "sepia/stt-server:dynamic_$version_aarch64" \
--amend "sepia/stt-server:dynamic_$version_armv7l" \
--amend "sepia/stt-server:dynamic_$version_amd64"

sudo docker manifest push sepia/stt-server:latest