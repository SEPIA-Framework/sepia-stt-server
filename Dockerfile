FROM debian:stretch-slim

### GET ALL PACKAGES ###

RUN apt-get update && apt-get install -y \
        git wget curl nano unzip \
        make automake autoconf \
        python2.7 python3 python-pip \
        gcc g++ gnupg \
		build-essential libboost-all-dev cmake zlib1g-dev libbz2-dev liblzma-dev \
		swig libpulse-dev libasound2-dev

RUN apt-get clean && apt-get autoclean && apt-get autoremove -y

### ZAMIA SPEECH / KALDI ###

RUN mkdir /apps && cd /apps && \
	echo "deb http://goofy.zamia.org/repo-ai/debian/stretch/amd64/ ./" >/etc/apt/sources.list.d/zamia-ai.list && \
	wget -qO - http://goofy.zamia.org/repo-ai/debian/stretch/amd64/bofh.asc | apt-key add - && \
	apt-get update && \
	apt-get install kaldi-chain-zamia-speech-de kaldi-chain-zamia-speech-en python-kaldiasr python-nltools pulseaudio-utils pulseaudio

### KenLM ###

RUN cd /apps && \
	wget -O - https://kheafield.com/code/kenlm.tar.gz |tar xz && \
	mkdir kenlm/build && cd kenlm/build && \
	cmake .. && make -j${nproc}

ENV PATH="/apps/kenlm/build/bin:${PATH}"

### Kaldi-adapt-lm ###

RUN cd /apps && \
	git clone https://github.com/fquirin/kaldi-adapt-lm.git && \
	cd kaldi-adapt-lm && \
	python setup.py install
	
### OpenFST (the one in 'opt/kaldi/tools' is not enough) ###

RUN cd /apps && mkdir openfst && cd openfst && \
	wget -O - http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.6.9.tar.gz |tar xz && \
	cd openfst-1.6.9 && \
	./configure --enable-far=true && \
	make -j${nproc} && make -j${nproc} install
	
ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"
RUN cd /apps && rm -r openfst

### SEPIA STT Server ###

RUN pip install tornado webrtcvad numpy
RUN cd /apps && \
	git clone https://github.com/SEPIA-Framework/sepia-stt-server.git
	
### Working folders ###
RUN mkdir /apps/share && mkdir /apps/share/kaldi_models && mkdir /apps/share/lm_corpus