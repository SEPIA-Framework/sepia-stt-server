#!/bin/bash
# paths
SCRIPT_PATH="$(realpath "$BASH_SOURCE")"
SCRIPT_FOLDER="$(dirname "$SCRIPT_PATH")"
cd "$SCRIPT_FOLDER"
log_date() {
	local NOW=$(date +"%Y_%m_%d_%H:%M:%S")
	echo "$NOW"
}
mkdir -p logs
if [ -f "log.out" ]; then
	cp log.out "logs/backup_$(log_date).out"
	rm log.out
fi
echo "Running SEPIA STT-Server"
echo "$(log_date) - Start" > log.out
cd server
nohup python3 -u -m launch &>> ../log.out &
sleep 3
cd ..
#bash status.sh
cat log.out
echo ""
