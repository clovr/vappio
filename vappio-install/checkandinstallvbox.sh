#!/bin/bash

ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`
if [ "$ipaddr" != "" ] 
    ls -L /etc/vappio/vbox/S05-vboxadd

    if [ "$?" != 0 ]
    then
	ls /etc/vappio/vbox/S05-vboxadd
	if [ "$?" != 0 ]
	then
	    /opt/vappio-install/recipes/vbox.sh yes
	fi
    fi
fi

