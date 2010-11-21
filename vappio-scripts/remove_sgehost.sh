#!/bin/bash
#remove_sgehost.sh $hostname [wait]
#optional wait indicates attempt to wait for jobs to be removed from the machine before rescheduling

deadhostname=$1
wait=$2

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##
master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
if [ "$master" = "$deadhostname" ]
then
    echo "Attempt to remove master $master, exiting"
    vlog "Attempt to remove master $master, exiting"
    exit 1
fi

vlog "Attempting to remove sge host $deadhostname"

##
#Attempt to reschedule jobs before removing host
#Steps are 
#1)disable queues so no new work runs here
#2)reschedule any remaining work
#3)optionally, wait for any pending outbound data transfer to finish
#4)remove host from master

#Disable all queues on this host

isactive=`$SGE_ROOT/bin/$ARCH/qhost -xml -q -h $deadhostname | xpath -e "//queue"`
vlog "Querying SGE for queues:$isactive"

if [ "$isactive" != "" ]
then
    $SGE_ROOT/bin/$ARCH/qmod -d "*@$deadhostname"
    vlog "Removing $deadhostname\n"
#Reschedule any running jobs on this machine
#This does not work for single hosts, rescheds all $SGE_ROOT/bin/$ARCH/qmod -f -rq $execq@$deadhostname
#$SGE_ROOT/bin/$ARCH/qmod -f -rq $stagingsubq@$myhostname
    $SGE_ROOT/bin/$ARCH/qstat -q $execq@$deadhostname -u '*' -xml | xpath -e "//JB_job_number/text()" | perl -ne 'print "qmod -f -rj $_"' | sh
    $SGE_ROOT/bin/$ARCH/qstat -q $stagingq@$deadhostname -u '*' -xml | xpath -e "//JB_job_number/text()" | perl -ne 'print "qmod -f -rj $_"' | sh
#Remove any other jobs on this host?
else
    $SGE_ROOT/bin/$ARCH/qmod -d "*@$deadhostname"
    vlog "Node not active, skipping"
fi

if [ "$wait" != "" ]
then
    #Keep checking over an interval, sleep on each iteration
    maxwait=10 #10*sleep 6=1 minute total waiting
    i=0
    while [ "$i" -le "$maxwait" ]
    do 
	vlog "Waiting for jobs to finish on host $deadhostname, iteration $i"
#Check for any jobs submitted from this host to finish. such jobs include wf transfer jobs stagingwf
	isrunning=0
	alljobs=`$SGE_ROOT/bin/$ARCH/qstat -u '*' | perl -ne 's/^\s+//;print' | cut -f 1 -d ' ' | perl -ne 'chomp;if(/(\d+)/){print "$1 "}'`
	for job in $alljobs
	do
	    runningjobs=`$SGE_ROOT/bin/$ARCH/qstat -j $job | grep sge_o_host | grep $deadhostname`
	    if [ "$runningjobs" != "" ]
	    then
		vlog "Job $job submitted from $deadhostname is still running"
		isrunning=1
	    fi
	done
    
	if [ $isrunning == 1 ]
	then
	    vlog "Jobs still running from submit host $deadhostname"
	else
	    jobs1=`$SGE_ROOT/bin/$ARCH/qstat -q $execq@$deadhostname -u '*'`
	    jobs2=`$SGE_ROOT/bin/$ARCH/qstat -q $stagingsubq@$deadhostname -u '*'`
	    if [ "$jobs1" == "" ] && [ "$jobs2" == "" ] 
	    then
		break;
	    fi
	fi
	i=`expr $i + 1`
	sleep 6
    done
fi

vlog "Removing $deadhostname from SGE"
#Remove host from SGE
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $deadhostname $stagingsubq
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $deadhostname $execq
$SGE_ROOT/bin/$ARCH/qconf -de $deadhostname
$SGE_ROOT/bin/$ARCH/qconf -ds $deadhostname
$SGE_ROOT/bin/$ARCH/qconf -kej $deadhostname
$SGE_ROOT/bin/$ARCH/qconf -dh $deadhostname
$SGE_ROOT/bin/$ARCH/qconf -dconf $deadhostname

#Occasionally, the host is known by another name to SGE
#Check for this and remove that name as well
alias=`$SGE_ROOT/utilbin/$ARCH/gethostbyname -name $deadhostname`
if [ "$alias" != "$deadhostname" ]
then
    $vappio_scripts/remove_sgehost.sh $alias
fi