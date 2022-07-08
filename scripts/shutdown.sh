#!/bin/bash
set -e
# A bit ugly but it works ^^
if [ $(pgrep -f "python3 -u -m launch" | wc -l) -gt 0 ]; then
	if [ $(pgrep -f "python3 -u -m launch" | xargs pwdx | grep "sepia-stt" | wc -l) -gt 0 ]; then
		PROC=$(pgrep -f "python3 -u -m launch" | xargs pwdx | grep "sepia-stt" | grep -Eo "^[0-9]*")
		echo "Stopping SEPIA STT-Server with process ID: $PROC ..."
		kill $PROC
		echo "DONE"
	else
		echo "No matching SEPIA STT-Server process found"
	fi
else
	echo "No SEPIA STT-Server process found"
fi
#ps aux | grep "python3 -u -m launch"
#pkill -f 'python3 -u -m launch'
