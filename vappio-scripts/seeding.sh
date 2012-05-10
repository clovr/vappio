#!/bin/bash

# USAGE:seeding.sh remotehost queue
#
# Seeding performs two actions
# 1)Copies data from master to $remotehost using $staging_script
# 2)Adds $remotehost to $queue
#
# After this script completes, the remotehost has been successfully
# staged and is ready to seed peers

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###"
vlog "### $0 aka seeding.sh (`whoami`) on `hostname` args: $1 $2 sge_job_id:$JOB_ID"
vlog "###"

remotehost=$1
queue=$2

#Stage data
vlog "Running staging for $remotehost"

#Loop updating staging dir until no changes
#Handles case where data is being written to the staging directory after starting staging_script
changes="yes"
maxretries=5
i=0
while [ "$changes" != "" ] && [ $i -le $maxretries ];
  do
  $staging_script $remotehost #1>> $vappio_log 2>> $vappio_log  
  ret=$?
  if [ $ret != 0 ]
  then
      changes="yes"
      vlog "ERROR: $0 staging fail. return value $ret"
      verror "STAGING FAILURE, in seeding loop"
      #Requeue job, RETRY_COUNT is already incremented by staging_script meaning we will have MAX_SGE_RETRIES/2
      rcount=`expr $RETRY_COUNT + 1` 
      if [ $rcount -gt $MAX_SGE_RETRIES ]
      then
	  vlog "Max retries $rcount > $MAX_SGE_RETRIES exceeded for $JOB_ID. Exit 1 from seeding.sh in loop"
	  exit 1
      else
	  vlog "Marking retry $rcount"
	  qalter -v RETRY_COUNT=$rcount $JOB_ID
	  exit 99
      fi
  else
      ret=0
      #Confirm that changes are non-null. List all changes between current host and remote host
      changes=`$rsynccmd -av -n -e "$ssh_client -i $ssh_key $ssh_options" --delete --size-only $staging_dir/ root@$remotehost:$staging_dir | grep -v "sending incremental file list" | grep -v "total size is" | grep -v "bytes/sec" | perl -ne 's/\s+//g;print'`
      vlog "Staging changes $changes"
  fi
  i=`expr $i + 1`
done

#At this point the staging directory is synced between remotehost and current host
#Add host back into the queue
if [ $ret = 0 ]
then
    vlog "staging successful"
    #Add to proper queue if not already added
    vlog "Adding $remotehost to $queue"
    $SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $remotehost $queue 
    #Make sure queue@host is enabled
    $SGE_ROOT/bin/$ARCH/qmod -e $queue@$remotehost
else
    vlog "ERROR: $0 staging fail. return value $ret"
    verror "SEEDING FAILURE 2";
    #Requeue job
    rcount=`expr $RETRY_COUNT + 1` 
    if [ $rcount -gt $MAX_SGE_RETRIES ]
    then
	vlog "Max retries $rcount > $MAX_SGE_RETRIES exceeded for $JOB_ID. Exit 1 from seeding.sh"
	exit 1
    else
	vlog "Marking retry $rcount, returning $ret from seeding.sh"
	qalter -v RETRY_COUNT=$rcount $JOB_ID
	exit $ret
    fi
fi

