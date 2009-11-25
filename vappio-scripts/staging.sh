#!/bin/sh
#Mirrors staging directory from the MASTER or DATA_NODE to an EXEC_NODE
#
#In the case where an EXEC_NODE is already staged, it can stage other nodes
#in a peer-to-peer manner. This is achieved through the stagingsub.q
#
#Invoked by workflow start, start_exec, and SGE prolog for the exec.q. 
#
#Scheduled through SGE running from staging.q(MASTER_NODE,DATA_NODE),stagingsub.q(EXEC_NODE).
#Note, the rsync is invoked so that the MASTER,DATA pushes data to the EXEC_NODE
#This allows for coordination of staging so that a configurable number of staging steps
#run concurrently as determined by the number of slots in the staging.q.

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###" 
vlog "### $0 (`whoami`) on `hostname`" 
vlog "###" 

remotehost="$1"

#copy staging area
vlog "Start staging from $staging_dir/ to $remotehost:$staging_dir"
#rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --delete $staging_dir/ $remotehost:$staging_dir 1>> $vappio_log 2>> $vappio_log
#cmd="rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" --delete $staging_dir/ root@$remotehost:$staging_dir"
vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" --delete $staging_dir/ root@$remotehost:$staging_dir"
rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --delete $staging_dir/ root@$remotehost:$staging_dir 1>> $vappio_log 2>> $vappio_log
vlog "rsync return value: $?"
