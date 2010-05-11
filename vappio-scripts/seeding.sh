#!/bin/sh

# USAGE:seeding.sh remotehost queue
#
# Seeding performs two actions
# 1)Copies data from master to $remotehost using $staging_script
# 2)Adds $remotehost to $queue

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

remotehost=$1
queue=$2

#Stage data
vlog "Running staging for $remotehost"

#Loop updating staging dir until no changes
#Handles case where data is being written to the staging directory after starting staging_script
changes="yes"

while [ "$changes" != "" ];
  do
  $staging_script $remotehost 1>> $vappio_log 2>> $vappio_log  
  #List all changes between current host and remote host
  changes=`rsync -av -n -e "$ssh_client -i $ssh_key $ssh_options" --delete --size-only $staging_dir/ root@$remotehost:$staging_dir | grep -v "sending incremental file list" | grep -v "total size is" | grep -v "bytes/sec" | perl -ne 's/\s+//g;print'` 
  echo "Changes $changes"
done

#At this point the staging directory is synced between remotehost and current host
#Add host back into the queue
if [ $? == 0 ]
then
    vlog "staging successful"
    #Add to proper queue if not already added
    vlog "Adding $remotehost to $queue"
    $SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $remotehost $queue 
    #Make sure queue@host is enabled
    $SGE_ROOT/bin/$ARCH/qmod -e $queue@$remotehost
else
    vlog "ERROR: $0 staging fail. return value $?"
    verror "SEEDING FAILURE";
    exit 1
fi

