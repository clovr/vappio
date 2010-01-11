#!/bin/sh
#syncdata.sh
#Mirrors the staging directory from the master 
#to the virtualized grid, including DATA_NODES (in staging.q)
#and EXEC_NODES (in stagingsub.q)
#
#First, removes all nodes from the staging queues
#Runs staging script to perform the mirror
#And add nodes back to the staging queues

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##
sync="n"
if [ $1 ]; then
    if [ "$1" == "--synchronous" ]; then
        sync="y"
    fi
fi

vlog "###" 
vlog "### $0 (`whoami`) on `hostname`" 
vlog "###" 

#This script should be run on the master
execnodes=`$vappio_scripts/printqueuehosts.pl $execq`

master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`

for node in $execnodes
 do
  vlog "Syncing ergatis directory to $node"
  rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --delete /opt/ergatis/ root@$node:/opt/ergatis 1>> $vappio_log 2>> $vappio_log
done
