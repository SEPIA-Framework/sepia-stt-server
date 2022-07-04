#!/bin/bash
IMAGE_TAG=
version=
if [ -n "$1" ]; then
	version=$1
else
	echo "Please specify the version, e.g. 'v1.0.0'"
	exit
fi
if [ -n "$(uname -m | grep aarch64)" ]; then
	IMAGE_TAG="dynamic_${version}_aarch64"
elif [ -n "$(uname -m | grep armv7l)" ]; then
	IMAGE_TAG="dynamic_${version}_armv7l"
else
	# NOTE: x86 32bit build not supported atm
	IMAGE_TAG="dynamic_${version}_amd64"
fi
sudo docker run --rm --name=sepia-stt-vosk -p 20741:20741 -it sepia/stt-server:"$IMAGE_TAG" /bin/bash
#-v share:/home/admin/share
