#!/usr/bin/env bash
# App Launch script - Exit Kodi to launch another program
# Updated by zachmorris for use with IAGL
# This script will try to exit Kodi first via JSONRPC, then a normal shutdown if the first attempt fails, then a hard shutdown if the second attempt fails

# Check for agruments
if [ -z "$*" ]; then
	echo "No arguments provided."
	echo "Usage:"
	echo "applaunch.sh [/path/to/]executable [arguments]"
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

#Start OSX Exit
if ! [ -z $KODI_PID_DARWIN ]
then
	echo "OSX Darwin Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5
	if ! [ -z $JSON_RPC_COMMAND ]
	then
		if ! [[ $JSON_RPC_COMMAND == *"$RPC_RESULT"* ]]
		then
			if ps -p $KODI_PID_DARWIN > /dev/null
			then
				echo "JSONRPC response was $JSON_RPC_COMMAND but Kodi is still running!"
			else
				KODI_EXIT="1"
			fi
		else
			echo "JSONRPC response was $JSON_RPC_COMMAND"
		fi

	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSONRPC exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_DARWIN 
		# Wait for the quit
		sleep 2
		if ps -p $KODI_PID_DARWIN > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_DARWIN
			# Wait for the kill
			sleep 2
			if ! ps -p $KODI_PID_DARWIN > /dev/null
			then
				echo "SIGKILL Exit Success"
				KODI_EXIT="1"
			fi
		else
			echo "SIGHUP Exit Success"
			KODI_EXIT="1"
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
fi
#End OSX Exit

#Start Linux Standalone
if ! [ -z $KODI_PID_LINUX_STANDALONE ]
then
	echo "Linux Standalone Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5
	if ! [ -z $JSON_RPC_COMMAND ]
	then
		if ! [[ $JSON_RPC_COMMAND == *"$RPC_RESULT"* ]]
		then
			KODI_EXIT="1"
		else
			echo "JSONRPC response was $JSON_RPC_COMMAND"
		fi

	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSONRPC exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_LINUX_STANDALONE 
		# Wait for the quit
		sleep 2
		if ps -p $KODI_PID_LINUX_STANDALONE > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_LINUX_STANDALONE
			# Wait for the kill
			sleep 2
			if ! ps -p $KODI_PID_LINUX_STANDALONE > /dev/null
			then
				echo "SIGKILL Exit Success"
				KODI_EXIT="1"
			fi
		else
			echo "SIGHUP Exit Success"
			KODI_EXIT="1"
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
fi
#End Linux Standalone


#Start Linux X11
if ! [ -z $KODI_PID_LINUX_X11 ]
then
	echo "Linux X11 Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5
	if ! [ -z $JSON_RPC_COMMAND ]
	then
		if ! [[ $JSON_RPC_COMMAND == *"$RPC_RESULT"* ]]
		then
			KODI_EXIT="1"
		else
			echo "JSONRPC response was $JSON_RPC_COMMAND"
		fi

	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSONRPC exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_LINUX_X11 
		# Wait for the quit
		sleep 2
		if ps -p $KODI_PID_LINUX_X11 > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_LINUX_X11
			# Wait for the kill
			sleep 2
			if ! ps -p $KODI_PID_LINUX_X11 > /dev/null
			then
				echo "SIGKILL Exit Success"
				KODI_EXIT="1"
			fi
		else
			echo "SIGHUP Exit Success"
			KODI_EXIT="1"
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
fi
#End Linux X11

#Start Linux X11
if ! [ -z $KODI_PID_LINUX ]
then
	echo "Linux Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5
	if ! [ -z $JSON_RPC_COMMAND ]
	then
		if ! [[ $JSON_RPC_COMMAND == *"$RPC_RESULT"* ]]
		then
			KODI_EXIT="1"
		else
			echo "JSONRPC response was $JSON_RPC_COMMAND"
		fi

	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSONRPC exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_LINUX 
		# Wait for the quit
		sleep 2
		if ps -p $KODI_PID_LINUX > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_LINUX
			# Wait for the kill
			sleep 2
			if ! ps -p $KODI_PID_LINUX > /dev/null
			then
				echo "SIGKILL Exit Success"
				KODI_EXIT="1"
			fi
		else
			echo "SIGHUP Exit Success"
			KODI_EXIT="1"
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
fi
#End Linux X11

# Start Emulator Launch
if ! [ -z $KODI_EXIT ]
then
	if ps -p $KODI_PID_DARWIN_HELPER > /dev/null
	then
		echo "Stopping XBMCHelper for OSX"
		kill -s SIGKILL $KODI_PID_DARWIN_HELPER
	fi
	echo "Kodi Exited, Launching Emulator with command: $@"
	# Launch app - escaped!
	"$@" &
	EMULATOR_PID=$!
	echo "Waiting for emulator to exit..."
	wait $EMULATOR_PID
	if [ $(echo "$SECONDS < 6" | bc) -ne 0  ]
	then
		#Something is wrong because it all happened too fast
		echo "There was likely an error while launching, waiting 10 seconds before restarting Kodi"
		sleep 10
	fi
	# Done? Restart Kodi
	sleep 1
	if ! [ -z $KODI_BIN_DARWIN ]
	then
		echo "Restarting OSX Kodi with: $KODI_BIN_DARWIN"
		nohup $KODI_BIN_DARWIN &
	fi
	if ! [ -z $KODI_BIN_LINUX ]
	then
		echo "Restarting Linux Kodi with: $KODI_BIN_LINUX"
		nohup $KODI_BIN_LINUX &
	fi
	#Attempt to restart IAGL after relaunching Kodi
	sleep 3
	RESTART_IAGL_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Addons.ExecuteAddon", "params": { "addonid": "plugin.program.iagl" },  "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	echo "JSONRPC response to restart IAGL was $RESTART_IAGL_RPC_COMMAND"
else
	echo "Kodi Never Exited, so I cant launch the emulator"
fi

#End of script