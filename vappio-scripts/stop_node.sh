#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

# Gather some data
myhostname=`hostname -f`

nodetype=`cat $vappio_runtime/node_type`
echo "Node is $nodetype. Shutting down"

case $nodetype in
    master) 
	$vappio_scripts/stop_master.sh
	;;
    exec) 
	$vappio_scripts/stop_exec.sh
	;;
    data) 
	$vappio_scripts/stop_data.sh
	;;
    OFFLINE) 
	echo "Node is already OFFLINE"
	;;
esac
