#!/bin/bash

#vappio_prolog.sh sge_job_dir command command_args
#
#Performs staging of data and Ergatis workflow files prior
#to execution of job "command command_args"
#
#This script is invoked from the prolog attached to the exec.q in
#the vappio framework

#The following error codes are supported
#              0: Success
#              99: Reschedule job
#              100: Put job in error state
#              Anything else: Put queue in error state

##
##Import vappio config
vappio_scripts=$vappio_root
source $vappio_scripts/vappio_config.sh
##
##

request_cwd=$1
command_str=$2
command_args=$3

myhost=`vhostname`
vlog "###" 
vlog "### $0 (`whoami`)" 
vlog "###" 

vlog "Running vappio prolog on host $myhost. Script arguments request_cwd=$request_cwd command_str=$command_str args=$command_args" 

#Only handle RunWorkflow commands submitted by Ergatis
#All other commands will do nothing
if [ "$command_str" == "RunWorkflow" ]
then
    vlog "This job appears to be submitted by Ergatis. Event log is $request_cwd" 

    mkdir -p $request_cwd 	 
    touch $request_cwd/event.log
    
    wfxml=`echo -E "$command_args" | perl -ne '$_ =~ s/\s+/ /g;@x=split(/[\s=]/,$_);%args=@x;print $args{"-i"},"\n"'`
    wfdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.*\/)/);print "$dir1$dir2"'`
    wfcomponentdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.*\/)/);print "$dir1"'`
    wfgroupdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.+)\//);print "$dir2"'`
    vlog "wfxml: $wfxml"
    vlog "wfdir: $wfdir"
    vlog "wfcomponentdir: $wfcomponentdir"
    vlog "wfgroupdir: $wfgroupdir"
    
    if [ -z "$wfdir" ]
    then
	verror "PROLOG. Unable to parse workflow directory from wfxml=$wfxml" 
	exit 100
    fi
    if [ -z "$wfgroupdir" ]
    then
	verror "PROLOG. Unable to parse group directory from wfxml=$wfxml" 
	exit 100
    fi
    echo "$wfdir" > $request_cwd/wfdir
    if [ $? -ne 0 ]
    then
        verror "PROLOG. Cannot save file $request_cwd/wfdir: $?"
        exit 100
    fi
    
    mkdir -p $wfdir
    if [ $? -ne 0 ]
    then
	verror "PROLOG. Cannot create directory $wfdir: $?"
	exit 100
    fi
    
    vlog "Submitting staging job for $wfxml@$myhost to wf.q" 
    #Get iterator input, workflow xml and final.config from the master to the exec host
    cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/bash -b n -sync y -q $wfq $stagingwf_script $myhost $wfxml"
    vlog "CMD: $cmd" 
    $cmd 1> stagingwf.qsub.$$.out 2> stagingwf.qsub.$$.stderr
    ret1=$?

    #Check for more error conditions
    #qsub returns 0 in some failure conditions, including if job is killed with qdel
    eout=`grep "Unable to run job" stagingwf.qsub.$$.out`
    vlog "Workflow staging ran with exit code $ret1 [$eout]"

    if [ $ret1 -ne 0 ] || [ "$eout" != "" ]
    then
	verror "PROLOG. Error during qsub return code: $ret1 [$eout]"
	#Requeue, entire job
	exit 99
    fi
    
    #Sync staging dir from any data node
    #vlog "Submitting staging job for staging_dir@$myhost" 
    #cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $stagingq,$stagingsubq $staging_script $myhost"
    #vlog "CMD: $cmd" 
    #$cmd 1>> $vappio_log 2>> $vappio_log
    
    #Previous steps should have completed, so now we should have all our inputs are are ready to run
    #Read the .final.config file to retrieve the output repository
    #First check if we are in a Ergatis group or not
    compconfigfile=`ls $wfcomponentdir/*.final.config`
    if [ "$compconfigfile" = "" ]
    then
	#It appears we are not in an Ergatis group
	wfcomponentdir=`dirname $wfxml`
	compconfigfile=`ls $wfcomponentdir/*.final.config`
	if [ "$compconfigfile" = "" ]
	then
	    verror "PROLOG. Unable to find component directory $wfcomponentdir or config file $wfcomponentdir/*.final.config" 
	    exit 100
	fi
	#Grab all output
	outprefix=`grep -P '^\s*.;OUTPUT_DIRECTORY.;\s*=' $wfcomponentdir/*.final.config | perl -ne 'split(/=/);print $_[1]'`
	outdir=`echo "$outprefix"`
    else
	#We are in an Ergatis group, grab group output only
	outprefix=`grep -P '^\s*.;OUTPUT_DIRECTORY.;\s*=' $wfcomponentdir/*.final.config | perl -ne 'split(/=/);print $_[1]'`
	outdir=`echo "$outprefix/$wfgroupdir"`
    fi
    if [ -z "$outprefix" ]
    then
	verror "PROLOG. Unable to parse output directory from $wfcomponentdir/*.final.config" 
	exit 100
    fi 
    #Save the output repository name to a file
    echo "$outdir" > $request_cwd/outdir
    if [ $? -ne 0 ]
    then
	verror "PROLOG. Unable to save output directory in file $request_cwd/outdir"
	exit 100
    fi 
    ##
    #Perform additional data staging if specified in the component configuration file
    #STAGEDATA=file1 file2 dir1 dir2
    #Files and directories should be absolute paths
    #Copies from submission host (usually master node) to $myhost
    stagedata=`grep STAGEDATA $wfcomponentdir/*.final.config | perl -ne 'split(/=/);print $_[1]'`
    if [ "$stagedata" != "" ]; then
	#verror "PROLOG. STAGEDATA configuration option not implemented"
	vlog "Submitting staging of input from $SGE_O_HOST to $myhost:$stagedata via $stagingq,$stagingsubq"
	cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -l hostname=$SGE_O_HOST -q $stagingq,$stagingsubq $staging_script $myhost $stagedata"
	vlog "CMD: $cmd" 
	$cmd #1>> $vappio_log 2>> $vappio_log
	if [ $? -ne 0 ]
	then
	    verror "PROLOG. Unable to copy $stagedata to $myhost"
	    exit 100
	fi 
	vlog "Finished staging of $f@$myhost"
    fi
    
fi

exit 0
