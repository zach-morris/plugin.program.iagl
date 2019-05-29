#!/bin/sh

if [ -f "/usr/bin/retroarch.start" ]
then
	# Launch app - escaped!
	systemd-run /usr/bin/retroarch.start "$@"
fi

if [ -f "/usr/bin/retroarch.sh" ]
then
	# Launch app - escaped!
	systemd-run /usr/bin/retroarch.sh "$@"
fi

# Done!