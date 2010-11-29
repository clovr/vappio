#!/bin/bash

#USAGE:vappio_epilog.sh hostname sge_job_dir command_str
#

##
##Import vappio config
vappio_scripts=$vappio_root
source $vappio_scripts/vappio_config.sh
##
##
exechost=$1
request_cwd=$2
command_str=$3
command_args=$4

vlog "###" 
vlog "### $0 (`whoami`)" 
vlog "###" 

myhost=`hostname -f`

vlog "Running epilog on $myhost. Script arguments exechost=$1 request_cwd=$2 command_str=$3 args=$4" 

#Attempt to harvest the output directory
#Only handle RunWorkflow commands submitted by Ergatis
#All other commands will skip harvesting output directory
if [ "$command_str" == "RunWorkflow" ]
then
    wfdir=`cat ${request_cwd}/wfdir`
    outdir=`cat ${request_cwd}/outdir`
    
    if [ -z "$wfdir" ]
    then
	verror "EPILOG. Unable to retrive wfdir from file ${request_cwd}/wfdir" 
	exit 100
    fi
    
    if [ -z "$outdir" ]
    then
	verror "EPILOG. Unable to retrive wfdir from file ${request_cwd}/outdir" 
	exit 100
    fi
    
    ##
    #Epilog past this point assumes workflow
    #wfxml=`echo -E "$command_args" | perl -ne '$_ =~ s/\s+/ /g;@x=split(/[\s=]/,$_);%args=@x;print $args{"-i"},"\n"'`
    #wfdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.*\/)/);print "$dir1$dir2"'`
    #wfcomponentdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.*\/)/);print "$dir1"'`
    #wfgroupdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.+)\//);print "$dir2"'`
    if [ ! -z "$wfcomponentdir" ]
    then
	harvestdata=`grep HARVESTDATA $wfcomponentdir/*.final.config | perl -ne 'split(/=/);print $_[1]'`
	if [ "$harvestdata" != "" ]; then
	    verror "EPILOG. HARVESTDATA configuration option not implemented"
#    vlog "Submitting harvesting of output $exechost:$outdir to $harvestingq"
#    cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync $waitonharvest -q $harvestingq $harvesting_script $exechost $harvestdata"
#    vlog "CMD: $cmd"
#    $cmd 1>> $vappio_log 2>> $vappio_log
#    ret1=$?
#    vlog "rsync return value: $?"
#    if [ $ret1 -ne 0 ]
#	then
#	verror "EPILOG Error during harvesting output $exechost:$outdir to $harvestingq"
#	exit 100
#    fi
	fi
    fi

    ##
    #Harvest output directory
    #$waitonharvest determines whether workflow will wait for harvesting 
    #to complete before marking the command complete
    vlog "Submitting harvesting of output $exechost:$outdir to $harvestingq"
    cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/bash -b n -sync $waitonharvest -q $harvestingq $harvesting_script $exechost $outdir"
    vlog "CMD: $cmd"
    $cmd #1>> $vappio_log 2>> $vappio_log
    ret1=$?
    vlog "rsync return value: $ret"
    if [ $ret1 -ne 0 ]
    then
	#Job error
	verror "EPILOG Error during harvesting data qsub return code: $ret1"
    fi
fi

#For all Workflow jobs, we need to harvest the event.log from the exec host
#For RunWorkflow jobs, we also need to harvest $wfdir set in the previous code block
#If this is a job submitted by Workflow, it must have an event.log. Otherwise, do nothing
if [ -f "${request_cwd}/event.log" ]
then
    #Harvest wf xml
    vlog "Submitting harvesting of workflow xml on $exechost:$wfdir to $wfq" 
    cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/bash -b n -sync y -q $wfq $harvestingwf_script $exechost \"$wfdir\" ${request_cwd}"
    vlog "CMD: $cmd" 
    $cmd #1>> $vappio_log 2>> $vappio_log
    ret2=$?
    vlog "rsync return value: $ret2"
    if [ $ret2 -ne 0 ]
    then
	verror "EPILOG Error during harvesting event.log qsub return code: $ret2"
	#Job error
    fi
fi

exit 0
