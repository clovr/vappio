#!/bin/sh
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###" 
vlog "### $0 (`whoami`) on `hostname`" 
vlog "###" 

#exec host is passed in on $1
exechost=$1
wfdir=$2
request_cwd=$3

hostname=`hostname -f`

vlog "Running harvestingwf.sh. Script arguments exechost=$1 wfdir=$2 request_cwd=$3"

parentdir=`echo "$wfdir" | perl -ne '/(.*\/)[^\/]+/;print $1'`

#Harvest workflow XML if this is a workflow command
if [ "$wfdir" != "" ] && [ -d "$parentdir" ]
then
    vlog "Harvesting workflow output from $exechost:$wfdir to $parentdir"
    mkdir -p $parentdir
    vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" root@$exechost:$wfdir $parentdir"
    rsync -av -e "$ssh_client -i $ssh_key $ssh_options" root@$exechost:$wfdir $parentdir 1>> $vappio_log 2>> $vappio_log
    if [ $? == 0 ]
    then
	vlog "rsync success. return value: $?"
    else
	vlog "ERROR: $0 rsync fail. return value: $?"
	verror "HARVESTING WF XML FAILURE"
        #requeue if certain conditions met
	isreachable=`printf "kv\nhostname=$exechost\n" | /opt/vappio-metrics/host-is-reachable | grep "reachable=yes"`
	if [ -d "${request_cwd}" ] && [ "$isreachable" = "" ]
	then
	    exit 99;
	else
	    exit 1;
	fi
    fi
fi

#Workflow uses event.log to store job states
#This file is critical for announcing job status to Workflow
vlog "Copying event.log from ${request_cwd}/event.log to ${request_cwd}/"
vlog "CMD: rsync -rlDvh -e \"$ssh_client -i $ssh_key $ssh_options\" root@$exechost:${request_cwd}/event.log ${request_cwd}/"
rsync -rlDvh -e "$ssh_client -i $ssh_key $ssh_options" root@$exechost:${request_cwd}/event.log ${request_cwd}/ 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value: $?"
    verror "HARVESTING WF event.log FAILURE"
    #requeue if certain conditions met
    isreachable=`printf "kv\nhostname=$exechost\n" | /opt/vappio-metrics/host-is-reachable | grep "reachable=yes"`
    if [ -d "${request_cwd}" ] && [ "$isreachable" = "" ]
    then
	echo "I~~~Failed to retrieve event.log from host $exechost" >> ${request_cwd}/event.log
	echo "I~~~host $exechost isreachable=$isreachable" >> ${request_cwd}/event.log
	echo "I~~~Rescheduling harvesting" >> ${request_cwd}/event.log
	exit 99;
    else
	#Print error to event.log
	echo "I~~~Failed to retrieve event.log from host $exechost" >> ${request_cwd}/event.log
	echo "I~~~host $exechost isreachable=$isreachable" >> ${request_cwd}/event.log
	exit 1;
    fi
fi
