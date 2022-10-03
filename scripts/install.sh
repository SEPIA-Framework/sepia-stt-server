#!/bin/bash
set -e
# paths
SCRIPT_PATH="$(realpath "$BASH_SOURCE")"
SCRIPT_FOLDER="$(dirname "$SCRIPT_PATH")"
# skip confirm question?
install_path="$SCRIPT_FOLDER"
code_branch="master"
autoconfirm=0
virtualenv=0
setup_type=1	# 1: all, 2: Vosk only
skip_adapt_scripts=""
asr_engine="dynamic"
while getopts yp:s:b:vh? opt; do
	case $opt in
		y) autoconfirm=1;;
		p) install_path="$OPTARG";;
		s) setup_type="$OPTARG";;
		b) code_branch="$OPTARG";;
		v) virtualenv=1;;
		?|h) printf "Usage: %s [-y] [-v] [-p path] [-s setup-type] [-b git-branch]\n" $0; exit 2;;
	esac
done
if [ -z "$setup_type" ] || [ "$setup_type" = "1" ]; then
	asr_engine="dynamic"
elif [ "$setup_type" = "2" ]; then
	asr_engine="vosk"
else
	echo "Unknown setup ID: ABORT"
	exit 1
fi
if [ "$autoconfirm" = "0" ]; then
	echo "This script will download the SEPIA STT-Server and try to install it locally."
	echo "Please clean-up the folder before if it contains an old installation!"
	echo ""
	echo "Install path (p): $install_path"
	echo "Code branch (b): $code_branch"
	echo "Use virtual env (v): $virtualenv"
	echo "Setup (s):"
	if [ "$asr_engine" = "dynamic" ]; then
		echo "- Engine: Dynamic (all)"
		echo "- Models: Vosk small (en, de), Coqui test (en)"
	elif [ "$asr_engine" = "vosk" ]; then
		echo "- Engine: Vosk (only)"
		echo "- Models: Vosk small (en, de)"
	fi
	if [ -z "$skip_adapt_scripts" ]; then
		echo "- Adapt-LM scripts: download"
	fi
	echo ""
	echo "NOTE: You can use the '-y' flag to automatically confirm all questions."
	echo "If you experience problems please consider using the Docker container or the latest Python Wheel files from the release."
	echo "Alternatively you can fallback to Vosk-only mode (-s 2) which is easier to install."
	echo ""
	read -p "Enter 'ok' to continue: " okabort
	echo ""
	if [ -n "$okabort" ] && [ $okabort = "ok" ]; then
		echo "Ok. Good luck ;-)"
	else
		echo "Np. Maybe later :-)"
		exit
	fi
	echo ""
fi
# install folder
mkdir -p "$install_path"
cd "$install_path"
#
echo "Installing Linux packages ..."
sudo apt update
sudo apt-get install -y --no-install-recommends git build-essential unzip procps python3-pip python3-dev python3-venv python3-setuptools python3-wheel libffi-dev
#amd64 only? libatlas-base-dev
echo ""
echo "Downloading STT-Server (branch: $code_branch) ..."
git clone --single-branch --depth 1 -b "$code_branch" https://github.com/SEPIA-Framework/sepia-stt-server.git
mv sepia-stt-server/src ./server
mv sepia-stt-server/scripts/run.sh ./
mv sepia-stt-server/scripts/shutdown.sh ./
mv sepia-stt-server/scripts/status.sh ./
rm -rf sepia-stt-server
echo ""
echo "Installing Python server requirements ..."
PLATFORM=""
if [ -n "$(uname -m | grep aarch64)" ]; then
	PLATFORM=aarch64
elif [ -n "$(uname -m | grep armv7l)" ]; then
	PLATFORM=armv7l
elif [ -n "$(uname -m | grep x86_64)" ]; then
	PLATFORM=amd64
elif [ -n "$(uname -m | grep armv6l)" ]; then
	echo "Platform: armv6l - NOT SUPPORTED"
	exit 1
else
	echo "Platform: x86_32 - NOT SUPPORTED"
	exit 1
fi
echo "Platform: $PLATFORM"
mkdir -p models
mkdir -p downloads
# Virtual env?
if [ "$virtualenv" = "1" ]; then
	if [ -d "venv" ]; then
		source "venv/bin/activate"
	else
		python3 -m venv "venv"
		source "venv/bin/activate"
	fi
fi
# Server
cd server
pip3 install --upgrade pip
pip3 install -r requirements_server.txt
# Vosk engine
if [ "$asr_engine" = "dynamic" ] || [ "$asr_engine" = "vosk" ]; then
	echo ""
	echo "Installing Vosk requirements ..."
	#currently aarch64 files are missing on PyPI
	#pip3 install -r requirements_vosk.txt
	vosk_wheel=""
	if [ "$PLATFORM" = "aarch64" ]; then
		vosk_wheel="vosk-0.3.42-py3-none-linux_aarch64.whl"
	elif [ "$PLATFORM" = "armv7l" ]; then
		vosk_wheel="vosk-0.3.42-py3-none-linux_armv7l.whl"
	else
		vosk_wheel="vosk-0.3.42-py3-none-linux_x86_64.whl"
	fi
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/$vosk_wheel
	pip3 install $vosk_wheel
	rm $vosk_wheel
fi
# Coqui engine
if [ "$asr_engine" = "dynamic" ] || [ "$asr_engine" = "coqui" ]; then
	echo ""
	echo "Installing Coqui requirements ..."
	pip3 install -r requirements_coqui.txt
fi
cd ..
cd downloads
# Vosk models
if [ "$asr_engine" = "dynamic" ] || [ "$asr_engine" = "vosk" ]; then
	echo ""
	echo "Downloading Vosk models ..."
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-en-us-0.15.zip
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-small-de-0.15.zip
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v0.9.5/vosk-model-spk-0.4.zip
	unzip vosk-model-small-en-us-0.15.zip && mv vosk-model-small-en-us-0.15 ../models/vosk-model-small-en-us
	unzip vosk-model-small-de-0.15.zip && mv vosk-model-small-de-0.15 ../models/vosk-model-small-de
	unzip vosk-model-spk-0.4.zip && mv vosk-model-spk-0.4 ../models/vosk-model-spk
fi
# Coqui models
if [ "$asr_engine" = "dynamic" ] || [ "$asr_engine" = "coqui" ]; then
	echo ""
	echo "Downloading Coqui models ..."
	wget https://github.com/SEPIA-Framework/sepia-stt-server/releases/download/v1.0.0/coqui-model-en-1.0.0.zip
	unzip coqui-model-en-1.0.0.zip && mv coqui-model-en-1.0.0 ../models/coqui-model-en
fi
cd ..
# Replace server config?
if [ "$asr_engine" = "vosk" ]; then
	echo ""
	echo "Adapting 'server.conf' file ..."
	mv server/server.conf server/server-dynamic.conf
	mv server/server-vosk.conf server/server.conf
fi
# LM Adapt scripts
if [ -z "$skip_adapt_scripts" ]; then
	echo ""
	echo "Downloading Adapt-LM scripts ..."
	ADAPT_LM_BRANCH=master
	git clone --single-branch --depth 1 -b $ADAPT_LM_BRANCH https://github.com/fquirin/kaldi-adapt-lm.git
	#cd kaldi-adapt-lm
	#bash 1-download-requirements.sh
	#rm *.tar.gz
	#cd ..
fi
echo ""
echo "DONE"
