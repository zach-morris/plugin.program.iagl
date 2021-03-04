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
KODI_PID_RPI=$(ps -A | grep [k]odi-rbp | head -1 | awk '{print $1}')
KODI_PID_RPI3=$(ps -A | grep [k]odi-rbp3 | head -1 | awk '{print $1}')
KODI_PID_RPI4=$(ps -A | grep [k]odi-rbp4 | head -1 | awk '{print $1}')
KODI_BIN_LINUX=""
KODI_BIN_RPI=""
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
if ! [ -z $KODI_PID_RPI ]
then
	KODI_BIN_RPI="kodi-rbp"
fi
if ! [ -z $KODI_PID_RPI3 ]
then
	KODI_BIN_RPI="kodi-rbp3"
fi
if ! [ -z $KODI_PID_RPI4 ]
then
	KODI_BIN_RPI="kodi-rbp4"
fi

#Sleep to let Kodi write to log, IAGL to complete, and whatnot prior to shutdown
sleep 1s

#Start OSX Exit
if ! [ -z $KODI_PID_DARWIN ]
then
	echo "OSX Darwin Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5s
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
		sleep 2s
		if ps -p $KODI_PID_DARWIN > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_DARWIN
			# Wait for the kill
			sleep 2s
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
	#Check if helper is still running, it may have been closed with JSON.  If not, kill it manually
	if ! [ -z $KODI_PID_DARWIN_HELPER ]
	then
		if ps -p $KODI_PID_DARWIN_HELPER > /dev/null
		then
			echo "Stopping XBMCHelper for OSX"
			kill -s SIGKILL $KODI_PID_DARWIN_HELPER
		fi
	fi
fi
#End OSX Exit

#Start Linux Standalone
if ! [ -z $KODI_PID_LINUX_STANDALONE ] && [ -z $KODI_EXIT ]
then
	echo "Linux Standalone Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5s
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
		if command -v kodi-send &> /dev/null
		then
			echo "JSON RPC exit failed, attempting kodi-send"
			kodi-send -a "ShutDown()"
			sleep 5s
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSON RPC / kodi-send exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_LINUX_STANDALONE 
		# Wait for the quit
		sleep 2s
		if ps -p $KODI_PID_LINUX_STANDALONE > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_LINUX_STANDALONE
			# Wait for the kill
			sleep 2s
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
		echo "JSON RPC / kodi-send Exit Success"
		KODI_EXIT="1"
	fi
fi
#End Linux Standalone


#Start Linux X11
if ! [ -z $KODI_PID_LINUX_X11 ] && [ -z $KODI_EXIT ]
then
	echo "Linux X11 Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5s
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
		if command -v kodi-send &> /dev/null
		then
			echo "JSON RPC exit failed, attempting kodi-send"
			kodi-send -a "ShutDown()"
			sleep 5s
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSON RPC / kodi-send exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_LINUX_X11 
		# Wait for the quit
		sleep 2s
		if ps -p $KODI_PID_LINUX_X11 > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_LINUX_X11
			# Wait for the kill
			sleep 2s
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
		echo "JSON RPC / kodi-send Exit Success"
		KODI_EXIT="1"
	fi
fi
#End Linux X11

#Start Linux
if ! [ -z $KODI_PID_LINUX ] && [ -z $KODI_EXIT ]
then
	echo "Linux Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5s
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
		if command -v kodi-send &> /dev/null
		then
			echo "JSON RPC exit failed, attempting kodi-send"
			kodi-send -a "ShutDown()"
			sleep 5s
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSON RPC / kodi-send exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_LINUX 
		# Wait for the quit
		sleep 2s
		if ps -p $KODI_PID_LINUX > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_LINUX
			# Wait for the kill
			sleep 2s
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
		echo "JSON RPC / kodi-send Exit Success"
		KODI_EXIT="1"
	fi
fi
#End Linux

#Start RPi
if ! [ -z $KODI_PID_RPI ] && [ -z $KODI_EXIT ]
then
	echo "Raspberry Pi Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5s
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
		if command -v kodi-send &> /dev/null
		then
			echo "JSON RPC exit failed, attempting kodi-send"
			kodi-send -a "ShutDown()"
			sleep 5s
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSON RPC / kodi-send exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_RPI 
		# Wait for the quit
		sleep 2s
		if ps -p $KODI_PID_RPI > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_RPI
			# Wait for the kill
			sleep 2s
			if ! ps -p $KODI_PID_RPI > /dev/null
			then
				echo "SIGKILL Exit Success"
				KODI_EXIT="1"
			fi
		else
			echo "SIGHUP Exit Success"
			KODI_EXIT="1"
		fi
	else
		echo "JSON RPC / kodi-send Exit Success"
		KODI_EXIT="1"
	fi
fi
#End RPi

#Start RPi3
if ! [ -z $KODI_PID_RPI3 ] && [ -z $KODI_EXIT ]
then
	echo "Raspberry Pi 3 Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5s
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
		if command -v kodi-send &> /dev/null
		then
			echo "JSON RPC exit failed, attempting kodi-send"
			kodi-send -a "ShutDown()"
			sleep 5s
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSON RPC / kodi-send  exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_RPI3 
		# Wait for the quit
		sleep 2s
		if ps -p $KODI_PID_RPI3 > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_RPI3
			# Wait for the kill
			sleep 2s
			if ! ps -p $KODI_PID_RPI3 > /dev/null
			then
				echo "SIGKILL Exit Success"
				KODI_EXIT="1"
			fi
		else
			echo "SIGHUP Exit Success"
			KODI_EXIT="1"
		fi
	else
		echo "JSON RPC / kodi-send  Exit Success"
		KODI_EXIT="1"
	fi
fi
#End RPi3

#Start RPi4
if ! [ -z $KODI_PID_RPI4 ] && [ -z $KODI_EXIT ]
then
	echo "Raspberry Pi 4 Detected"
	echo "Attempting to exit Kodi via JSONRPC"
	JSON_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	# Wait for the quit
	sleep 5s
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
		if command -v kodi-send &> /dev/null
		then
			echo "JSON RPC exit failed, attempting kodi-send"
			kodi-send -a "ShutDown()"
			sleep 5s
		fi
	else
		echo "JSONRPC Exit Success"
		KODI_EXIT="1"
	fi
	if [ -z $KODI_EXIT ]
	then
		echo "JSON RPC / kodi-send exit failed, attempting SIGHUP"
		kill -s SIGHUP $KODI_PID_RPI4 
		# Wait for the quit
		sleep 2s
		if ps -p $KODI_PID_RPI4 > /dev/null
		then
			echo "SIGHUP exit failed, attempting SIGKILL"
			kill -s SIGKILL $KODI_PID_RPI4
			# Wait for the kill
			sleep 2s
			if ! ps -p $KODI_PID_RPI4 > /dev/null
			then
				echo "SIGKILL Exit Success"
				KODI_EXIT="1"
			fi
		else
			echo "SIGHUP Exit Success"
			KODI_EXIT="1"
		fi
	else
		echo "JSON RPC / kodi-send Exit Success"
		KODI_EXIT="1"
	fi
fi
#End RPi4

# Start Emulator Launch
if ! [ -z $KODI_EXIT ]
then
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
		sleep 10s
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
	if ! [ -z $KODI_BIN_RPI ]
	then
		echo "Restarting RPi Kodi with: $KODI_BIN_RPI"
		nohup $KODI_BIN_RPI &
	fi
	#Attempt to restart IAGL after relaunching Kodi
	sleep 5s
	RESTART_IAGL_RPC_COMMAND=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Addons.ExecuteAddon", "params": { "addonid": "plugin.program.iagl" },  "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
	echo "JSONRPC response to restart IAGL was $RESTART_IAGL_RPC_COMMAND"
else
	echo "Kodi Never Exited, so I cant launch the emulator"
fi

#End of script