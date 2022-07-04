#!/bin/bash
IMAGE_TAG=latest
HOST_MODELS="$(realpath ~)/stt/models"
HOST_SHARE="$(realpath ~)/stt/share"
mkdir -p "$HOST_MODELS"
mkdir -p "$HOST_SHARE"
sudo docker run --rm --name=sepia-stt -p 20741:20741 -it \
	-v "$HOST_MODELS":/home/admin/sepia-stt/models/my \
	-v "$HOST_SHARE":/home/admin/sepia-stt/share \
	--env SEPIA_STT_SETTINGS=/home/admin/sepia-stt/share/my.conf \
	sepia/stt-server:$IMAGE_TAG \
	/bin/bash
