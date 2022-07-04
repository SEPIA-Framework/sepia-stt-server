FROM debian:buster-slim

# Default to UTF-8 file.encoding
ENV LANG C.UTF-8

# Run 1
RUN echo 'Installing dependencies...' && \
#
#   Dependencies
    apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo git wget curl nano unzip zip procps \
    build-essential \
    python3-pip python3-dev python3-setuptools python3-wheel \
    #amd64 only? moved to adapt package: libatlas-base-dev \
    libffi-dev && \
    pip3 install pip --upgrade && \
#
#   Fast-API
    pip3 install cffi && \
    pip3 install fastapi uvicorn[standard] aiofiles && \
#
#   Clean up
    apt-get remove -y build-essential && \
    apt-get install libatomic1 && \
    apt-get clean && apt-get autoclean && apt-get autoremove -y && \
#
#   Create user
    useradd --create-home --shell /bin/bash admin && \
    adduser admin sudo && \
    echo "admin ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
#
#   ENV
#SOME_ENV_VAR=/...my-stuff

#   USER
USER admin

# Run 1
RUN echo "Installing Vosk ..." && \
	mkdir -p /home/admin/install && \
	mkdir -p /home/admin/sepia-stt/models && \
	mkdir -p /home/admin/kaldi-adapt-lm && \
	cd /home/admin/install && \
	if [ -n "$(uname -m | grep aarch64)" ]; then \
		echo "Downloading Vosk 0.3.42 for aarch64"; \
		#wget https://github.com/alphacep/vosk-api/releases/download/v0.3.42/vosk-0.3.42-py3-none-linux_aarch64.whl; \
		wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/vosk-0.3.42-py3-none-linux_aarch64.whl; \
		pip3 install vosk-0.3.42-py3-none-linux_aarch64.whl; \
	elif [ -n "$(uname -m | grep armv7l)" ]; then \
		echo "Downloading Vosk 0.3.42 for armv7l"; \
		#wget https://github.com/alphacep/vosk-api/releases/download/v0.3.42/vosk-0.3.42-py3-none-linux_armv7l.whl; \
		wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/vosk-0.3.42-py3-none-linux_armv7l.whl; \
		pip3 install vosk-0.3.42-py3-none-linux_armv7l.whl; \
	else \
		echo "Downloading Vosk 0.3.42 for x86_64"; \
		#wget https://github.com/alphacep/vosk-api/releases/download/v0.3.42/vosk-0.3.42-py3-none-linux_x86_64.whl; \
		wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/vosk-0.3.42-py3-none-linux_x86_64.whl; \
		pip3 install vosk-0.3.42-py3-none-linux_x86_64.whl; \
	fi && \
	#wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip && \
	#wget https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip && \
	#wget https://alphacephei.com/vosk/models/vosk-model-spk-0.4.zip && \
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-en-us-0.15.zip && \
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-de-0.15.zip && \
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-spk-0.4.zip && \
	unzip vosk-model-small-en-us-0.15.zip && \
	mv vosk-model-small-en-us-0.15 /home/admin/sepia-stt/models/vosk-model-small-en-us && \
	unzip vosk-model-small-de-0.15.zip && \
	mv vosk-model-small-de-0.15 /home/admin/sepia-stt/models/vosk-model-small-de && \
	unzip vosk-model-spk-0.4.zip && \
	mv vosk-model-spk-0.4 /home/admin/sepia-stt/models/vosk-model-spk && \
#
	echo "Installing Coqui-STT ..." && \
	if [ -n "$(uname -m | grep aarch64)" ]; then \
		echo "Downloading Coqui-STT 1.3.0 for aarch64"; \
		#wget https://github.com/coqui-ai/STT/releases/download/v1.3.0/stt-1.3.0-cp37-cp37m-linux_aarch64.whl; \
		wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/stt-1.3.0-cp37-cp37m-linux_aarch64.whl; \
		pip3 install stt-1.3.0-cp37-cp37m-linux_aarch64.whl; \
	elif [ -n "$(uname -m | grep armv7l)" ]; then \
		echo "Downloading Coqui-STT 1.3.0 for armv7l"; \
		#wget https://github.com/coqui-ai/STT/releases/download/v1.3.0/stt-1.3.0-cp37-cp37m-linux_armv7l.whl; \
		wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/stt-1.3.0-cp37-cp37m-linux_armv7l.whl; \
		wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/numpy-1.21.6-cp37-cp37m-linux_armv7l.whl; \
		pip3 install numpy-1.21.6-cp37-cp37m-linux_armv7l.whl; \
		pip3 install stt-1.3.0-cp37-cp37m-linux_armv7l.whl; \
	else \
		echo "Downloading Coqui-STT 1.3.0 for x86_64"; \
		#wget https://github.com/coqui-ai/STT/releases/download/v1.3.0/stt-1.3.0-cp37-cp37m-manylinux_2_24_x86_64.whl; \
		wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/stt-1.3.0-cp37-cp37m-manylinux_2_24_x86_64.whl; \
		pip3 install stt-1.3.0-cp37-cp37m-manylinux_2_24_x86_64.whl; \
	fi && \
	#mkdir -p /home/admin/sepia-stt/models/coqui-model-en && \
	#cd /home/admin/sepia-stt/models/coqui-model-en && \
	#wget https://coqui.gateway.scarf.sh/english/coqui/v1.0.0-large-vocab/model.tflite && \
	#cd /home/admin/install && \
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/coqui-model-en-1.0.0.zip && \
	unzip coqui-model-en-1.0.0.zip && \
	mv coqui-model-en-1.0.0 /home/admin/sepia-stt/models/coqui-model-en && \
#
	echo "Installing SEPIA STT ..." && \
	SEPIA_STT_BRANCH=master && \
	git clone --single-branch --depth 1 -b $SEPIA_STT_BRANCH https://github.com/SEPIA-Framework/sepia-stt-server.git && \
	mv sepia-stt-server/src /home/admin/sepia-stt/server && \
#
	echo "Installing Adapt-LM scripts ..." && \
	cd /home/admin && \
	ADAPT_LM_BRANCH=master && \
	git clone --single-branch --depth 1 -b $ADAPT_LM_BRANCH https://github.com/fquirin/kaldi-adapt-lm.git && \
	cd kaldi-adapt-lm && \
	bash 1-download-requirements.sh && \
	rm *.tar.gz && \
#
#	Clean up install folder
	cd /home/admin && \
	sudo rm -rf /home/admin/install && \
#
# TODO: install proxy with self-signed certs?
#
	echo "#!/bin/bash" > on-docker.sh && echo "cd sepia-stt/server && python3 -m launch" >> on-docker.sh
	
# Start
WORKDIR /home/admin
CMD bash on-docker.sh
