#!/bin/bash
# App Launch script - Quit Kodi to launch another program within Retropie

# Try and shutdown via curl first, http control must be enabled in Kodi service settings
result=$(curl -s --data-binary '{"jsonrpc": "2.0", "method": "Application.Quit", "id":1}' -H 'content-type: application/json;' http://127.0.0.1:8080/jsonrpc)
# Wait for the quit
sleep 3

KODI_PID=$(pidof kodi-rbpi_v7)
ES_PID=$(pidof emulationstation)

# Shutdown Kodi
if ! [ -z $KODI_PID ]
then
	kill -s SIGHUP $KODI_PID 
	echo "Kodi shutdown nice"
fi
# Shutdown ES
if ! [ -z $ES_PID ]
then
	kill -s SIGHUP $ES_PID 
	echo "ES shutdown nice"
fi
# Wait for the kill
sleep 1

#Is Kodi still running?  If so try shutdown hard
if ! [ -z $KODI_PID ]
then
	if ps -p $KODI_PID > /dev/null
	then
		kill -s SIGKILL $KODI_PID 
		echo "Kodi shutdown nice"
	fi
fi
#Is ES still running?  If so try shutdown hard
if ! [ -z $ES_PID ]
then
	if ps -p $ES_PID > /dev/null
	then
		kill -s SIGKILL $ES_PID 
		echo "ES shutdown nice"
	fi
fi
# Wait for the kill
sleep 1

if [ -f "/opt/retropie/supplementary/runcommand/runcommand.sh" ]
then
	# Launch app - escaped!
	/opt/retropie/supplementary/runcommand/runcommand.sh "$@"
	# Done? Restart Kodi
	/opt/retropie/supplementary/runcommand/runcommand.sh 0 _PORT_ kodi
fi

if [ -f "/opt/retroarena/supplementary/runcommand/runcommand.sh" ]
then
	# Launch app - escaped!
	/opt/retroarena/supplementary/runcommand/runcommand.sh "$@"
	# Done? Restart Kodi
	/opt/retroarena/supplementary/runcommand/runcommand.sh 0 _PORT_ kodi
fi

# Done!