#!/bin/sh
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
vlog "### $0 (`whoami`) on `hostname`" 
vlog "###" 

#exec host is passed in on $1
exechost=$1
dir=$2

parentdir=`echo "$dir" | perl -ne '/(.*\/)[^\/]+/;print $1'`

#harvest output
vlog "Harvesting output from $exechost:$dir to $parentdir"
mkdir -p $parentdir
vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" root@$exechost:$dir $parentdir"
rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --temp-dir $scratch_dir root@$exechost:$dir $parentdir 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value: $?"
    verror "HARVESTING FAILURE"
    #requeue if certain conditions met
    isreachable=`printf "kv\nhostname=$exechost\n" | /opt/vappio-metrics/host-is-reachable | grep "reachable=yes"`
    if [ -d "$parentdir" ] && [ "$isreachable" = "" ]
    then
	exit 99
    else
	exit 1
    fi
fi