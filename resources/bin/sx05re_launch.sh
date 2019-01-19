#!/bin/sh

#/bin/mkdir -p /storage/emulators/retroarch/system
#/bin/mkdir -p /storage/emulators/retroarch/screenshots

. /etc/profile

systemd-run /storage/.kodi/addons/plugin.program.iagl/resources/bin/sx05re.start "$@"