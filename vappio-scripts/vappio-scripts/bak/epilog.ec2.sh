#!/bin/sh
##
##BEGIN CONFIGURATION SETTINGS
export SGE_ROOT=/opt/sge
export SGE_CELL=default
ARCH=`$SGE_ROOT/util/arch`
vappio_scripts=/opt/vappio-scripts

ssh_key=/home/guest/.ssh/guest
#ssh-hpn is high performance ssh
ssh_client=/usr/local/bin/ssh-hpn
#turn off ssh encryption for faster transfer on trusted networks
ssh_options="-oNoneSwitch=yes -oNoneEnabled=yes"

harvestingq=transferin.q
harvesting_script=$vappio_scripts/harvesting.sh
waitonharvest=n
##END CONFIGURATION SETTING
##
echo "Running epilog on host $1"

echo "Submitting harvesting job for $wfdir@$1 and $outdir@$1"
master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
wfdir=`cat ${request_cwd}/wfdir`;
outdir=`cat ${request_cwd}/outdir`;
$SGE_ROOT/bin/$ARCH/qsub -S /bin/sh -b n -sync $waitonharvest -q $harvestingq $harvesting_script $1 $wfdir $outdir 

array_job() {
    local RV=1
    if [ "$SGE_TASK_ID" = "undefined" ]; then
        RV=0
    fi
    return $RV
}

print_eventinfo () {
    # If the environment variable SGE_TASK_ID is defined then it
    # is an array job, so print the task id 
    if [ "$ARRAY" = "0" ]; then
	header="${htc_id}~~~${sge_id}~~~${start_date}"
    else
	header="${htc_id}~~~${sge_id}.${SGE_TASK_ID}~~~${start_date}"
    fi
    message="job finished on $queue for $job_owner";

    echo "I~~~epilog starting";
    echo "I~~~htc id   sge id[.task id]   date   message   hostname"
    echo "T~~~${header}~~~$message~~~$hostname"
    echo "I~~~epilog ending";
}

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
    else
        # The job *IS* an array job
        EVENT_LOG="${request_cwd}/event.log.$SGE_TASK_ID"
    fi

    if [ -w "$EVENT_LOG" ] && [ -n "$htc_id" ]; then
        print_eventinfo >> "$EVENT_LOG" 2>&1
    fi
fi > /dev/null 2>&1

#This copies back event.log(s) to signal job completions in WF
echo "Coping event.log from ${request_cwd}/event.log to $master:${request_cwd}/"
date
rsync -rlDvh -e "$ssh_client -i $ssh_key $ssh_options" ${request_cwd}/event.log $master:${request_cwd}/
date
