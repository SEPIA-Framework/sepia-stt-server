#!/bin/bash
if [ -n "$(uname -m | grep aarch64)" ]; then
	IMAGE_TAG=vosk_aarch64
elif [ -n "$(uname -m | grep armv7l)" ]; then
	IMAGE_TAG=vosk_armv7l
else
	# NOTE: x86 32bit build not supported atm
	IMAGE_TAG=vosk_amd64
fi
sudo docker run --rm --name=sepia-stt-vosk -p 20741:20741 -it sepia/stt-server:$IMAGE_TAG /bin/bash
#-v share:/home/admin/share
