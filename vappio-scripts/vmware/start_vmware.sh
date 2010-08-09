#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/vmware/vmware_config.sh

# Mount VMware shared areas

if [ -f $vappio_runtime/no_dns ]
then
    nodns=1
fi

if [ "$nodns" == 1 ]
then
    touch $vappio_runtime/no_dns
fi

