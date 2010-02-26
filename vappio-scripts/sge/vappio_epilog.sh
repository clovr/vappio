#!/bin/sh
##
##Import vappio config
vappio_scripts=$vappio_root
source $vappio_scripts/vappio_config.sh
##
##
exechost=$1
request_cwd=$2

vlog "###" 
vlog "### $0 (`whoami`)" 
vlog "###" 

myhost=`hostname -f`

vlog "Running epilog on $myhost. Script arguments exechost=$1 request_cwd=$2" 

wfdir=`cat ${request_cwd}/wfdir`
outdir=`cat ${request_cwd}/outdir`

if [ -z "$wfdir" ]
then
	vlog "Unable to retrive wfdir from file ${request_cwd}/wfdir" 
	exit 1;
fi

if [ -z "$outdir" ]
then
    vlog "Unable to retrive wfdir from file ${request_cwd}/outdir" 
    exit 1;
fi

#Harvest output directory
vlog "Submitting harvesting of output $exechost:$outdir to $harvestingq"
cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync $waitonharvest -q $harvestingq $harvesting_script $exechost $outdir"
vlog "CMD: $cmd"
$cmd 1>> $vappio_log 2>> $vappio_log
ret1=$?
vlog "rsync return value: $ret"
if [ $ret1 -ne 0 ]
then
 vlog "Error during harvesting data qsub return code: $ret1"
 exit $ret1
fi

#Harvest wf xml
vlog "Submitting harvesting of workflow xml on $exechost:$wfdir to $wfq" 
cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $wfq $harvestingwf_script $exechost $wfdir ${request_cwd}"
vlog "CMD: $cmd" 
$cmd 1>> $vappio_log 2>> $vappio_log
ret2=$?
vlog "rsync return value: $ret2"
f [ $ret2 -ne 0 ]
then
 vlog "Error during harvesting workflow qsub return code: $ret2"
 exit $ret2
fi

exit
