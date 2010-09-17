#!/bin/bash
#remove_sgehost.sh $hostname [wait]
#optional wait indicates attempt to wait for jobs to be removed from the machine before rescheduling

deadhostname=$1
wait=$2

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

##
#Attempt to reschedule jobs before removing host
#Steps are 
#1)disable queues so no new work runs here
#2)reschedule any remaining work
#3)optionally, wait for any pending outbound data transfer to finish
#4)remove host from master

#Disable all queues on this host
echo "Removing dead host $deadhostname\n"
$SGE_ROOT/bin/$ARCH/qmod -d "*@$deadhostname"
#Reschedule any running jobs on this machine
$SGE_ROOT/bin/$ARCH/qmod -f -rq $execq@$deadhostname
$SGE_ROOT/bin/$ARCH/qmod -f -rq $stagingsubq@$myhostname
#Remove any other jobs on this host?

if [ "$wait" != "" ]
then
    #Keep checking over an interval, sleep on each iteration
    maxwait=10 #10*sleep 6=1 minute total waiting
    i=0
    while [ "$i" -le "$maxwait" ]
    do 
#Check for any jobs submitted from this host to finish. such jobs include wf transfer jobs stagingwf
	isrunning=0
	alljobs=`$SGE_ROOT/bin/$ARCH/qstat -u '*' | perl -ne 's/^\s+//;print' | cut -f 1 -d ' ' | perl -ne 'chomp;if(/(\d+)/){print "$1 "}'`
	for job in $alljobs
	do
	    runningjobs=`$SGE_ROOT/bin/$ARCH/qstat -j $job | grep sge_o_host | grep $deadhostname`
	    if [ "$runningjobs" != "" ]
	    then
		echo "Job $job submitted from $deadhostname is still running"
		isrunning=1
	    fi
	done
    
	if [ $isrunning == 1 ]
    then
	    vlog "Jobs still running from this submit host"
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

#Remove host from SGE
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $deadhostname $stagingsubq
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $deadhostname $execq
$SGE_ROOT/bin/$ARCH/qconf -de $deadhostname
$SGE_ROOT/bin/$ARCH/qconf -ds $deadhostname
$SGE_ROOT/bin/$ARCH/qconf -kej $deadhostname
$SGE_ROOT/bin/$ARCH/qconf -dh $deadhostname