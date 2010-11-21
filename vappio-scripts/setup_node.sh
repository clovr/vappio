#!/bin/bash

# Much of this is based on rc.local from the old Amazon vappio AMIs

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/clovrEnv.sh
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 aka setup_node.sh (`whoami`)"
vlog "###"

# Gather some data
myhostname=`hostname -f`

if [ ! -n "$myhostname" ]; then
    vlog "No valid hostname. Cannot configure node"
    echo "No valid hostname. Cannot configure node"
    exit 1 ;
fi


# Check variables that would probably have be set in run_user_data
if [ ! -n "$MASTER_NODE" ]; then
	vlog "Setting MASTER_NODE to default value $default_master_node"
	MASTER_NODE=$default_master_node
else
	vlog "MASTER_NODE was set to $MASTER_NODE"
fi
echo "$MASTER_NODE" > $vappio_runtime/master_node

if [ ! -n "$DATA_NODE" ]; then
        vlog "No DATA_NODE value passed"
else
        vlog "DATA_NODE was set to $DATA_NODE"
fi

if [ ! -n "$EXEC_NODE" ]; then
        vlog "No EXEC_NODE value passed"
else
        vlog "EXEC_NODE was set to $EXEC_NODE"
fi

# Perform specific node configurations
case $MASTER_NODE in
  localhost)
	echo "Configuring localhost as MASTER_NODE"
    vlog "Configuring localhost as MASTER_NODE"
    $vappio_scripts/start_master.sh #1>> $vappio_log 2>> $vappio_log
  ;;
esac

case $EXEC_NODE in
  localhost)
    vlog "Configuring localhost as EXEC_NODE"
    $vappio_scripts/start_exec.sh $MASTER_NODE #1>> $vappio_log 2>> $vappio_log
  ;;
esac

case $DATA_NODE in
  localhost)
    vlog "Configuring localhost as DATA_NODE"
    $vappio_scripts/start_data.sh $MASTER_NODE #1>> $vappio_log 2>> $vappio_log
  ;;
esac

