#!/bin/bash
#Copies harvesting directory from an EXEC_NODE to a DATA_NODE, or the MASTER
#

#Invoked by SGE epilog and runs on a MASTER_NODE or DATA_NODE as
#scheduled through SGE harvesting.q.  The rsync is invoked so that the
#MASTER_NODE/DATA_NODE pulls data from the EXEC_NODE

#This allows for coordination of harvesting so that a configurable
#number of harvesting steps run concurrently as determined by the
#number of slots in the harvesting.q.

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###" 
vlog "### $0 aka harvesting.sh (`whoami`) on `hostname` args: $1 $2 sge_job_id:$JOB_ID" 
vlog "###" 

#exec host is passed in on $1
exechost=$1
dir=$2

parentdir=`echo "$dir" | perl -ne '/(.*\/)[^\/]+/;print $1'`

#harvest output
vlog "Harvesting output from $exechost:$dir to $parentdir"
mkdir -p $parentdir
vlog "CMD: $rsynccmd -av -e \"$ssh_client -i $ssh_key $ssh_options\" root@$exechost:$dir $parentdir"
$rsynccmd -av -e "$ssh_client -i $ssh_key $ssh_options" --temp-dir $scratch_dir root@$exechost:$dir $parentdir 
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value: $?"
    verror "HARVESTING FAILURE for $dir"
    #requeue if certain conditions met
    isreachable=`printf "kv\nhostname=$exechost\n" | /opt/vappio-metrics/host-is-reachable | grep "reachable=yes"`
    direxists=`$ssh_client -o BatchMode=yes -i $ssh_key $ssh_options root@$exechost ls -d $dir`
    if [ -d "$parentdir" ] && [ "$isreachable" != "" ] && [ "$direxists" = "$dir" ]
    then
	#retry, directory appears to be online
	vlog "Attempting rescheduling of harvesting job"
	exit 99
    else
	#output directory missing, fail silently allowing resched of workflow job
	if [ -d "$parentdir" ] && [ "$isreachable" != "" ] && [ "$direxists" != "$dir" ]
	then
	    #TODO, if workflow is complete then must mark incomplete before resume
	    vlog "No output directory on remote host $exechost: $direxists != $dir " 
	    exit 1
	else
	    #job error
	    vlog "Aborting harvesting job"
	    exit 1
	fi
    fi
fi