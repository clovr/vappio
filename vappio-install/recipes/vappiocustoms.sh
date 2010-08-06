#!/bin/bash

#To recreate
#echo "CloVR" > etc/appliance_name
#echo "base" > etc/bundle_name
#date +%m%d%Y > etc/release_name


/etc/init/
/etc/hosts.orig
/etc/sudoers
/etc/update-motd.d/10-help-text
/etc/issue
/etc/vappio/bundle_name,release_name,appliance_name

rm /etc/update-motd.d/51_update-motd
rm /etc/update-motd.d/92-uec-upgrade-available
