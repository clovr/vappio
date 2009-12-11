#!/bin/sh

#vappio_prolog.sh sge_job_dir command command_args
#
#Performs staging of data and Ergatis workflow files prior
#to execution of job "command command_args"
#
#This script is invoked from the prolog attached to the exec.q in
#the vappio framework

##
##Import vappio config
vappio_scripts=$vappio_root
source $vappio_scripts/vappio_config.sh
##
##

request_cwd=$1
command_str=$2
command_args=$3

myhost=`hostname -f`
vlog "###" 
vlog "### $0 (`whoami`)" 
vlog "###" 

vlog "Running vappio prolog on host $myhost. Script arguments request_cwd=$request_cwd command_str=$command_str args=$command_args" 

#Only handle RunWorkflow commands submitted by Ergatis
#All other commands will do nothing
if [ "$command_str" == "RunWorkflow" ]
then
    vlog "This job appears to be submitted by Ergatis. Running directory is $request_cwd" 
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

	echo "$wfdir" > $request_cwd/wfdir
	if [ -z "$wfdir" ]
	then
		vlog "Unable to parse workflow directory from wfxml=$wfxml" 
		exit 1;
	fi
    	if [ -z "$wfgroupdir" ]
	then
		vlog "Unable to parse group directory from wfxml=$wfxml" 
		exit 1;
	fi
	 
	mkdir -p $wfdir
	vlog "Submitting staging job for $wfxml@$myhost to wf.q" 
	#Get workflow xml and final.config from the master to the exec host
        cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $wfq $stagingwf_script $myhost $wfxml"
	vlog "CMD: $cmd" 
	$cmd 1>> $vappio_log 2>> $vappio_log
	#Sync staging dir from any data node
	#vlog "Submitting staging job for staging_dir@$myhost" 
        #cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $stagingq,$stagingsubq $staging_script $myhost"
        #vlog "CMD: $cmd" 
	#$cmd 1>> $vappio_log 2>> $vappio_log
	vlog "Skipping re-staging of staging_dir@$myhost"

        #Previous steps should have completed, so now we should have all our inputs are are ready to run
	#First read the .final.config file to retrieve the output repository 
        outprefix=`grep OUTPUT_DIRECTORY $wfcomponentdir/*.final.config | perl -ne 'split(/=/);print $_[1]'`
        outdir=`echo "$outprefix/$wfgroupdir"`
	if [ -z "$outprefix" ]
	then
		vlog "Unable to parse output directory from $wfcomponentdir/*.final.config" 
		exit 1;
	fi 
	#Save the output repository name to a file
        echo "$outdir" > $request_cwd/outdir
fi

