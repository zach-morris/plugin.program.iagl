#!/bin/bash
# App Launch script - Quit Kodi to launch another program
# Thanks to rodalpho @ # http://xbmc.org/forum/showthread.php?t=34635
# By Redsandro 	2008-07-07
# By ryosaeba87	2010-08-24 (Added support for MacOSX)
# By malte 2015-01-22 (change from XBMC to Kodi)
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
		Kodi_PID=$(ps -A | grep [k]odi.bin | head -1 | awk '{print $1}')
		if [ -n $Kodi_standalone_PID ]
		then
			Kodi_BIN="kodi-standalone"
		else
			Kodi_BIN="kodi"
		fi
		;;	
	*)
		echo "I don't support this OS!"
		exit 1
		;;
esac

#echo $Kodi_BIN

# Is Kodi running?
if [ -n $Kodi_PID ]
then
	if [ -n $Kodi_standalone_PID ]
	then
		kill -SIGSTOP $Kodi_standalone_PID # STOP nice
	fi
	kill -SIGSTOP $Kodi_PID # STOP nice
	echo "STOP nice"
else
	echo "This script should only be run from within Kodi."
	exit
fi

# Wait for the STOP
sleep 1

echo "$@"

# Launch app - escaped!
"$@"

# Done? Restart Kodi
if [ -n $Kodi_PID ]
then
	if [ -n $Kodi_standalone_PID ]
	then
		kill -SIGCONT $Kodi_standalone_PID & # START nice
	fi
	kill -SIGCONT $Kodi_PID & # START nice
	echo "START nice"
else
	echo "This script should only be run from within Kodi."
	exit
fi