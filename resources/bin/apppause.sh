#!/usr/bin/env bash
# App Pause script - Exit Kodi to launch another program
# Updated by zachmorris for use with IAGL
# This script will try to pause Kodi and then launch your emulator, then unpause Kodi

# Check for agruments
if [ -z "$*" ]; then
	echo "No arguments provided."
	echo "Usage:"
	echo "apppause.sh [/path/to/]executable [arguments]"
	exit
fi

JSON_RPC_NOTIFICATION=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "GUI.ShowNotification", "params": {"title": "Please Wait", "message": "Running IAGL Launch Script" },  "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
SECONDS=0
KODI_PID_DARWIN=$(ps -A | grep [K]odi | grep -v [H]elper | head -1 | awk '{print $1}')
KODI_PID_DARWIN_HELPER=$(ps -A | grep [K]odi | grep [H]elper | head -1 | awk '{print $1}')
KODI_BIN_DARWIN=""
KODI_PID_LINUX_STANDALONE=$(ps -A | grep [k]odi-standalone | head -1 | awk '{print $1}')
KODI_PID_LINUX_X11=$(ps -A | grep [k]odi-x11 | head -1 | awk '{print $1}')
KODI_PID_LINUX=$(ps -A | grep [k]odi | head -1 | awk '{print $1}')
KODI_BIN_LINUX=""
KODI_EXIT=""
RPC_RESULT="\x22result\x22:\x22OK\x22"

if ! [ -z $KODI_PID_DARWIN ]
then
	KODI_BIN_DARWIN=$(ps -A | grep [K]odi | grep -v [H]elper | head -1 | awk '{print $4}')
fi
if ! [ -z $KODI_PID_LINUX_STANDALONE ]
then
	KODI_BIN_LINUX="kodi-standalone"
fi
if ! [ -z $KODI_PID_LINUX_X11 ]
then
	KODI_BIN_LINUX="kodi"
fi
if ! [ -z $KODI_PID_LINUX ]
then
	KODI_BIN_LINUX="kodi"
fi

#Sleep to let Kodi write to log
sleep 1

#Start OSX Pause
if ! [ -z $KODI_PID_DARWIN ]
then
	echo "OSX Darwin Detected"
	kill -s SIGSTOP $KODI_PID_DARWIN 
	# Wait for the pause
	sleep 2
fi
#End OSX

#Start Linux Standalone Pause
if ! [ -z $KODI_PID_LINUX_STANDALONE ]
then
	echo "Linux Standalone Detected"
	kill -s SIGSTOP $KODI_PID_LINUX_STANDALONE 
	# Wait for the pause
	sleep 2
fi
#End Linux Standalone

#Start Linux X11 Pause
if ! [ -z $KODI_PID_LINUX_X11 ]
then
	echo "Linux X11 Detected"
	kill -s SIGSTOP $KODI_PID_LINUX_X11 
	# Wait for the pause
	sleep 2
fi
#End Linux X11

#Start Linux Pause
if ! [ -z $KODI_PID_LINUX ]
then
	echo "Linux Detected"
	kill -s SIGSTOP $KODI_PID_LINUX 
	# Wait for the pause
	sleep 2
fi
#End Linux

# Start Emulator Launch
echo "Kodi Paused, Launching Emulator with command: $@"
# Launch app - escaped!
"$@" &
EMULATOR_PID=$!
echo "Waiting for emulator to exit..."
wait $EMULATOR_PID
if [ $(echo "$SECONDS < 6" | bc) -ne 0  ]
then
	#Something is wrong because it all happened too fast
	echo "There was likely an error while launching, waiting 5 seconds before unpausing Kodi"
	sleep 5
fi
# Done? Restart Kodi
sleep 1
#Start OSX UnPause
if ! [ -z $KODI_PID_DARWIN ]
then
	# echo "OSX Darwin Detected"
	kill -s SIGCONT $KODI_PID_DARWIN 
	# Wait for the UnPause
	sleep 1
fi
#End OSX

#Start Linux Standalone UnPause
if ! [ -z $KODI_PID_LINUX_STANDALONE ]
then
	# echo "Linux Standalone Detected"
	kill -s SIGCONT $KODI_PID_LINUX_STANDALONE 
	# Wait for the UnPause
	sleep 1
fi
#End Linux Standalone

#Start Linux X11 UnPause
if ! [ -z $KODI_PID_LINUX_X11 ]
then
	# echo "Linux X11 Detected"
	kill -s SIGCONT $KODI_PID_LINUX_X11 
	# Wait for the UnPause
	sleep 1
fi
#End Linux X11

#Start Linux UnPause
if ! [ -z $KODI_PID_LINUX ]
then
	# echo "Linux Detected"
	kill -s SIGCONT $KODI_PID_LINUX 
	# Wait for the UnPause
	sleep 1
fi
#End Linux

#End of script