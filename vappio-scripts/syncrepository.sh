#!/bin/bash
#Mirrors harvested data to the master
#This ensures that data harvested on a DATA_NODE is correctly
#harvested back to the master node
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###" 
vlog "### $0 (`whoami`) on `hostname`" 
vlog "###" 

remotehost=$1
vlog "Syncing repository from $remotehost:$harvesting_dir/ to $harvesting_dir" 
vlog "CMD: $rsynccmd -av -e \"$ssh_client -i $ssh_key $ssh_options\" root@$remotehost:$harvesting_dir/ $harvesting_dir"
$rsynccmd -av -e "$ssh_client -i $ssh_key $ssh_options" root@$remotehost:$harvesting_dir/ $harvesting_dir 1>> $vappio_log 2>> $vappio_log
vlog "rsync return value: $?"
