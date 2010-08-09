#!/bin/sh


# Mount VMware shared areas

if [ -f $vappio_runtime/no_dns ]
then
    nodns=1
fi



if [ "$nodns" == 1 ]
then
    touch $vappio_runtime/no_dns
fi

