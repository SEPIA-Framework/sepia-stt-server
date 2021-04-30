#!/bin/bash
# TODO: make version number variable
if [ -n "$(uname -m | grep aarch64)" ]; then
	sudo docker run --rm --name=vosk -p 20741:8080 -it sepia/stt-server:vosk_0.3.21_aarch64 /bin/bash
elif [ -n "$(uname -m | grep armv7l)" ]; then
	sudo docker run --rm --name=vosk -p 20741:8080 -it sepia/stt-server:vosk_0.3.21_armv7l /bin/bash
else
	# NOTE: x86 32bit build not supported atm
	sudo docker run --rm --name=vosk -p 20741:8080 -it sepia/stt-server:vosk_0.3.21_x86_64 /bin/bash
fi
#sudo docker run --rm --name=sepia_stt -p 20741:8080 -it -v share:/home/admin/share sepia/stt-server:vosk_0.3.21_armv7l /bin/bash
