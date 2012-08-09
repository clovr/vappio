#!/bin/bash

##
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

request_cwd=$1

fline=`grep "F~~~" ${request_cwd}/event.log`; 
if [ "$fline" = "" ]; 
then 
    echo "F~~~000~~~1~~~Mon Jan 1 00:00:00 UTC 1970~~~command finished~~~1" >> ${request_cwd}/event.log; 
fi        

