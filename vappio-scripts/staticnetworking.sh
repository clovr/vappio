#!/bin/bash

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

#requires format
#        address 192.168.0.100
#        netmask 255.255.255.0
#        network 192.168.0.0
#        broadcast 192.168.0.255
#        gateway 192.168.0.1

if [ -f "$vappio_userdata/static_ip" ]
then
    cp /etc/network/interfaces /etc/network/interfaces.bak
    echo "auto eth0" >> /etc/network/interfaces
    echo "iface eth0 inet static" >> /etc/network/interfaces
    cat $vappio_userdata/static_ip >> /etc/network/interfaces
else
    if [ -f "/etc/network/interfaces.bak" ]
    then
	cp /etc/network/interfaces.bak /etc/network/interfaces
    fi
fi
/etc/init.d/networking restart