#!/bin/sh

systemd-run /usr/bin/retroarch.start "$@"
systemd-run /usr/bin/retroarch.sh "$@"
