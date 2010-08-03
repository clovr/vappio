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
dir=$2
request_cwd=$3

hostname=`hostname -f`

vlog "Running harvestingwf.sh. Script arguments exechost=$1 dir=$2 request_cwd=$3"

parentdir=`echo "$dir" | perl -ne '/(.*\/)[^\/]+/;print $1'`

#harvest output
vlog "Harvesting workflow output from $exechost:$dir to $parentdir"
mkdir -p $parentdir
vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" root@$exechost:$dir $parentdir"
rsync -av -e "$ssh_client -i $ssh_key $ssh_options" root@$exechost:$dir $parentdir 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value: $?"
    verror "HARVESTING WF XML FAILURE"
    exit 1;
fi

vlog "Copying event.log from ${request_cwd}/event.log to ${request_cwd}/"
vlog "CMD: rsync -rlDvh -e \"$ssh_client -i $ssh_key $ssh_options\" root@$exechost:${request_cwd}/event.log ${request_cwd}/"
rsync -rlDvh -e "$ssh_client -i $ssh_key $ssh_options" root@$exechost:${request_cwd}/event.log ${request_cwd}/ 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value: $?"
    verror "HARVESTING WF event.log FAILURE"
    exit 1;
fi
