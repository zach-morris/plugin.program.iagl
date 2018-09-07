#!/bin/bash
# App Launch script - Pause Kodi to launch another program
# Updated by zachmorris for use with IAGL

# Check for agruments
if [ -z "$*" ]; then
	echo "No arguments provided."
	echo "Usage:"
	echo "applaunch.sh [/path/to/]executable [arguments]"
	exit
fi

case "$(uname -s)" in
	Darwin)
		Kodi_PID=$(ps -A | grep [K]odi | grep -v [H]elper | head -1 | awk '{print $1}')
		Kodi_BIN=$(ps -A | grep [K]odi | grep -v [H]elper | head -1 | awk '{print $4}')
		;;
	Linux)
		Kodi_standalone_PID=$(ps -A | grep [k]odi-standalone | head -1 | awk '{print $1}')
		Kodi_PID=$(ps -A | grep [k]odi-x11 | head -1 | awk '{print $1}')
		if [ -z $Kodi_PID ]
		then
			Kodi_PID=$(ps -A | grep [k]odi | head -1 | awk '{print $1}')
		fi
		if [ -z $Kodi_standalone_PID ]
		then
			Kodi_BIN="kodi"
		else
			Kodi_BIN="kodi-standalone"
		fi
		;;	
	*)
		echo "I don't support this OS!"
		exit 1
		;;
esac

# PAUSE Kodi
if ps -p $Kodi_PID > /dev/null
then
	if ! [ -z $Kodi_standalone_PID ]
	then
		kill -s SIGSTOP $Kodi_standalone_PID 
		echo "Pausing Kodi Standalone"
	fi
	if ! [ -z $Kodi_PID ]
	then
		kill -s SIGSTOP $Kodi_PID 
		echo "Pausing Kodi"
	fi
fi


# Wait for the STOP
sleep 1

echo "$@"

# Launch app - escaped!
"$@"

# Done? Unpause Kodi
if ps -p $Kodi_PID > /dev/null
then
	if ! [ -z $Kodi_standalone_PID ]
	then
		kill -s SIGCONT $Kodi_standalone_PID 
		echo "Continuing Kodi Standalone"
	fi
	if ! [ -z $Kodi_PID ]
	then
		kill -s SIGCONT $Kodi_PID 
		echo "Continuing Kodi"
	fi
fi