#!/bin/bash
IMAGE_TAG=latest
sudo docker run --rm --name=sepia-stt-vosk -p 20741:20741 -it sepia/stt-server:$IMAGE_TAG /bin/bash
#-v share:/home/admin/share
