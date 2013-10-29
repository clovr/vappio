#!/bin/bash

#Requires /etc/vappio

#Enable autologin for terminal
rm -f /etc/init/tty1.conf
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/init/tty1.conf /etc/init/tty1.conf
#perl -pi -e 's/^exec.*/exec \/sbin\/mingetty \-\-autologin root tty1/' /etc/init/tty1.conf

