#!/bin/sh
##
##BEGIN CONFIGURATION SETTINGS
export SGE_ROOT=/opt/sge
export SGE_CELL=default
ARCH=`$SGE_ROOT/util/arch`
vappio_scripts=/opt/vappio-scripts
staging_dir=/mnt/staging
harvesting_dir=/mnt/harvesting
wfworking_dir=/mnt/wf-working

ssh_key=/home/guest/.ssh/guest
#ssh-hpn is high performance ssh
ssh_client=/usr/local/bin/ssh-hpn
#turn off ssh encryption for faster transfer on trusted networks
ssh_options="-oNoneSwitch=yes -oNoneEnabled=yes"

stagingq=transferout.q
staging_script=$vappio_scripts/staging.sh
##END CONFIGURATION SETTING
##

echo "Running prolog on host $1"

#mkdir -p $harvesting_dir
#mkdir -p $staging_dir
#mkdir -p $wfworking_dir
#chmod 777 $harvesting_dir
#chmod 777 $staging_dir 
#chmod 777 $wfworking_dir 

master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
myhost=`hostname -f`

mkdir -p $request_cwd

echo "command_str=$command_str args=$command_args"

if [ $command_str == 'RunWorkflow' ]
then
	wfxml=`echo -E "$command_args" | perl -ne '$_ =~ s/\s+/ /g;@x=split(/[\s=]/,$_);%args=@x;print $args{"-i"},"\n"'`
        wfdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.*\/)/);print "$dir1$dir2"'`
	wfcomponentdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.*\/)/);print "$dir1"'`
	wfgroupdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.+)\//);print "$dir2"'`

	echo "$wfdir" > $request_cwd/wfdir

	mkdir -p $wfdir
	echo "Submitting staging job for $wfxml@$myhost to transferout.q"
	$SGE_ROOT/bin/$ARCH/qsub -S /bin/sh -b n -sync y -q $stagingq $staging_script $wfxml $myhost
	#staging.sh should have written the .final.config file. 
	#We can read this file to find the output directory
	outprefix=`grep OUTPUT_DIRECTORY $wfcomponentdir/*.final.config | perl -ne 'split(/=/);print $_[1]'`
	outdir=`echo "$outprefix/$wfgroupdir"` 
	echo "$outdir" > $request_cwd/outdir
fi


array_job() {
    local RV=1
    if [ "$SGE_TASK_ID" = "undefined" ]; then
        RV=0
    fi
    return $RV
}

print_eventinfo () {

    # Check if this job is restarting for some reason. If it is
    # restarting, then sleep upto 60 seconds before contine to
    # execute the job. This is a hack to make sure the original
    # is killed before the rescheduled job starts running.
    # and the rescheduled job
    #
    if [ $RESTARTED -eq 1 ]; then
        echo "I~~~`date`~~~This job has restarted for some reason.";
        echo "I~~~`date`~~~Sleeping for 60 seconds to make sure the original job is killed.";
        sleep 60;
    fi
    # If the environment variable SGE_TASK_ID is defined then it
    # is an array job, so print the task id
    if [ "$ARRAY" = "0" ]; then
        header="${htc_id}~~~${sge_id}~~~${start_date}"
    else
        header="${htc_id}~~~${sge_id}.${SGE_TASK_ID}~~~${start_date}"
    fi

    message="job started on $queue for $job_owner";

    echo "I~~~prolog starting";
    echo "I~~~htc id   sge id[.task id]   date   message   hostname"
    echo "S~~~${header}~~~$message~~~$hostname"
    echo "I~~~prolog ending";
}


# Determine our variables.
start_date=`date`;
hostname=$1
job_owner=$2
sge_id=$3
job_name=$4
queue=$5

# Determine if this is an array job
array_job
ARRAY=$?

if [ -n "$request_cwd" ]; then
    if [ "$ARRAY" = "0" ]; then
        # The job is *NOT* an array job
        EVENT_LOG="${request_cwd}/event.log"
	touch $EVENT_LOG
    else
        # The job *IS* an array job
        EVENT_LOG="${request_cwd}/event.log"
	touch $EVENT_LOG
    fi
    if [ -w "$EVENT_LOG" ] && [ -n "$htc_id" ]; then
        print_eventinfo >> "$EVENT_LOG" 2>&1
    fi
fi > /dev/null 2>&1

vappio_scripts=/opt/vappio-scripts
$vappio_scripts/vappio_prolog.sh $request_cwd $command_str "$command_args"
rsync -rlDvh -e "$ssh_client -i $ssh_key $ssh_options" ${request_cwd}/event.log $master:${request_cwd}/

exit 0

