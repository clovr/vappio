#!/bin/bash

ls -L /etc/vappio/vbox/S05-vboxadd

if [ "$?" != 0 ]
then
    /opt/vappio-install/recipes/vbox.sh yes
fi
