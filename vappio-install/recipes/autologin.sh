#!/bin/bash

#Requires /etc/vappio

#Enable autologin for terminal
rm -f /etc/init/tty1.conf
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init/tty1.conf /etc/init/tty1.conf
#perl -pi -e 's/^exec.*/exec \/sbin\/mingetty \-\-autologin root tty1/' /etc/init/tty1.conf

