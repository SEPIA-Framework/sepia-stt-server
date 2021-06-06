FROM debian:stretch-slim

# Get all packages

RUN apt-get update && apt-get install -y \
        git wget curl nano unzip \
        make automake autoconf \
        python2.7 python3 python-pip \
        gcc g++ gnupg \
        build-essential libboost-all-dev cmake zlib1g-dev libbz2-dev liblzma-dev \
        swig libpulse-dev libasound2-dev \
		libatlas-base-dev \
        nginx && \
#
#   Pips for STT Server
    pip install tornado webrtcvad numpy && \
#
#   Clean up
    apt-get clean && apt-get autoclean && apt-get autoremove -y && \
#
#   Working folders
    mkdir /apps && mkdir /apps/share && mkdir /apps/share/kaldi_models && mkdir /apps/share/lm_corpus

# Zamia Speech / Kaldi

RUN cd /apps && \
    echo "deb http://goofy.zamia.org/repo-ai/debian/stretch/amd64/ ./" >/etc/apt/sources.list.d/zamia-ai.list && \
    wget -qO - http://goofy.zamia.org/repo-ai/debian/stretch/amd64/bofh.asc | apt-key add - && \
    apt-get update && \
    apt-get install -y  python-kaldiasr python-nltools pulseaudio-utils pulseaudio && \
    apt-get clean && apt-get autoclean && apt-get autoremove -y && \
#
#   Download model
    mkdir /apps/tmp && cd /apps/tmp && \
    wget http://goofy.zamia.org/zamia-speech/asr-models/kaldi-generic-en-tdnn_f-r20190227.tar.xz && \
    tar -xf kaldi-generic-en-tdnn_f-r20190227.tar.xz && \
    mkdir /opt/kaldi/model && \
    mv kaldi-generic-en-tdnn_f-r20190227 /opt/kaldi/model/kaldi-generic-en-tdnn_f && \
    rm -r /apps/tmp

# KenLM

RUN cd /apps && \
    wget -O - https://kheafield.com/code/kenlm.tar.gz |tar xz && \
    mkdir kenlm/build && cd kenlm/build && \
    cmake .. && make -j${nproc}

ENV PATH="/apps/kenlm/build/bin:${PATH}"

# Kaldi-adapt-lm

RUN cd /apps && \
    git clone https://github.com/fquirin/kaldi-adapt-lm.git && \
    cd kaldi-adapt-lm && \
    python setup.py install && \
    rm -r .git && \
#
#   OpenFST (the one in 'opt/kaldi/tools' is not enough)
    cd /apps && mkdir openfst && cd openfst && \
    wget -O - http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-1.6.9.tar.gz |tar xz && \
    cd openfst-1.6.9 && \
    ./configure --enable-far=true && \
    make -j${nproc} && make -j${nproc} install && \
    cd /apps && rm -r openfst

ENV LD_LIBRARY_PATH="/usr/local/lib:${LD_LIBRARY_PATH}"

# SEPIA STT Server

RUN cd /apps && \
	mkdir tmp && cd tmp && \
    git clone https://github.com/SEPIA-Framework/sepia-stt-server.git && \
	cd .. && mv tmp/sepia-stt-server/legacy-server sepia-stt-server && \
    rm -r tmp && \
    ln -sf /apps/sepia-stt-server/nginx_config/stt /etc/nginx/sites-enabled/stt

# Start
WORKDIR /apps/sepia-stt-server
CMD service nginx start && python sepia_stt_server.py
