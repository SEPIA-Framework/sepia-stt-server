#!/bin/bash
if [ -n "$(uname -m | grep aarch64)" ]; then
	sudo docker run --rm --name=sepia-stt-vosk -p 20741:20741 -it sepia/stt-server:vosk_aarch64 /bin/bash
elif [ -n "$(uname -m | grep armv7l)" ]; then
	sudo docker run --rm --name=sepia-stt-vosk -p 20741:20741 -it sepia/stt-server:vosk_armv7l /bin/bash
else
	# NOTE: x86 32bit build not supported atm
	sudo docker run --rm --name=sepia-stt-vosk -p 20741:20741 -it sepia/stt-server:vosk_amd64 /bin/bash
fi
#sudo docker run --rm --name=sepia-stt -p 20741:20741 -it -v share:/home/admin/share sepia/stt-server:vosk_armv7l /bin/bash
