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
if [ "$nodetype" != "OFFLINE" ]
    then
    case `cat $vappio_runtime/node_type` in
	master) 
	    echo "Node is MASTER_NODE. Shutting down"
	    $vappio_scripts/stop_master.sh
	    ;;
	exec) 
	    echo "Node is EXEC_NODE. Shutting down"
	    $vappio_scripts/stop_exec.sh
	    ;;
	data) 
	    echo "Node is DATA_NODE. Shutting down"
	    $vappio_scripts/stop_data.sh
	    ;;
	OFFLINE) 
	    echo "Node is OFFLINE. Shutting down"
	    ;;
    esac
fi
