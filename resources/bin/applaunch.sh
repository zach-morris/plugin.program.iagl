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

# Shutdown Kodi
if ps -p $Kodi_PID > /dev/null
then
	if ! [ -z $Kodi_standalone_PID ]
	then
		kill -s SIGHUP $Kodi_standalone_PID 
		#kill -1 $Kodi_standalone_PID # Shutdown nice (SIGHUP)
		echo "Standalone shutdown nice"
	fi
	if ! [ -z $Kodi_PID ]
	then
		kill -s SIGHUP $Kodi_PID 
		#kill -1 $Kodi_PID # Shutdown nice (SIGHUP)
		echo "Shutdown nice"
	fi
#else
#	echo "This script should only be run from within Kodi."
#	exit
fi

# Wait for the kill
sleep 1

# Is Kodi still running?
if ps -p $Kodi_PID > /dev/null
then
	echo "Kodi is still running, attempting to KILL it"
	if ! [ -z $Kodi_standalone_PID ]
	then
		kill -s SIGKILL $Kodi_standalone_PID 
		#kill -9 $Kodi_standalone_PID # Shutdown nice (SIGHUP)
		echo "Standalone shutdown hard"
	fi
	if ! [ -z $Kodi_PID ]
	then
		kill -s SIGKILL $Kodi_PID 
		#kill -1 $Kodi_PID # Shutdown nice (SIGHUP)
		echo "Shutdown hard"
	fi
#else
#	echo "This script should only be run from within Kodi."
#	exit
fi

echo "$@"

# Launch app - escaped!
"$@"

# Done? Restart Kodi
$Kodi_BIN &