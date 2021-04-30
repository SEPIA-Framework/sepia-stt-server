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
	 libffi-dev && \
#
#   Clean up
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
	mkdir -p /home/admin/vosk && cd /home/admin/vosk && \
	pip3 install cffi && \
	if [ -n "$(uname -m | grep aarch64)" ]; then \
		echo "Downloading Vosk 0.3.21 for aarch64"; \
		wget https://github.com/alphacep/vosk-api/releases/download/0.3.21/vosk-0.3.21-py3-none-linux_aarch64.whl; \
		pip3 install vosk-0.3.21-py3-none-linux_aarch64.whl; \
	elif [ -n "$(uname -m | grep armv7l)" ]; then \
		echo "Downloading Vosk 0.3.21 for armv7l"; \
		wget https://github.com/alphacep/vosk-api/releases/download/0.3.21/vosk-0.3.21-py3-none-linux_armv7l.whl; \
		pip3 install vosk-0.3.21-py3-none-linux_armv7l.whl; \
	else \
		echo "Downloading Vosk 0.3.21 for x86_64"; \
		wget https://github.com/alphacep/vosk-api/releases/download/0.3.21/vosk-0.3.21-py3-none-manylinux2010_x86_64.whl; \
		pip3 install vosk-0.3.21-py3-none-manylinux2010_x86_64.whl; \
	fi && \
	git clone https://github.com/alphacep/vosk-api && \
	cd vosk-api/python/example && \
	wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.15.zip && \
	unzip vosk-model-small-en-us-0.15.zip && \
	mv vosk-model-small-en-us-0.15 model && \
	rm vosk-model-small-en-us-0.15.zip && \
	echo "vosk-model-small-en-us-0.15" > active_model && \
	echo "#!/bin/bash" > test.sh && echo "python3 ./test_simple.py test.wav" >> test.sh
	
# Start
WORKDIR /home/admin
CMD /bin/bash
