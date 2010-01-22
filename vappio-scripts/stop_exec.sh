#/bin/bash

#stop_exec.sh 
#Stops a Vappio exec host

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

myhostname=`hostname -f`

##
#Attempt to reschedule jobs before removing host
#Steps are 
#1)disable queues so no new work runs here
#2)reschedule any remaining work
#3)wait for any pending outbound data transfer to finish

vlog "Attempting to disable queue for host $myhostname"
$SGE_ROOT/bin/$ARCH/qmod -d $execq@$myhostname
$SGE_ROOT/bin/$ARCH/qmod -d $stagingsubq@$myhostname
vlog "Attempting to delete jobs for host $myhostname"
execjobs=`$SGE_ROOT/bin/$ARCH/qstat -q $execq@$myhostname -u '*' | perl -ne 's/^\s+//;print' | cut -f 1 -d ' ' | perl -ne 'chomp;if(/(\d+)/){print "$1 "}'`
if [ "$execjobs" != "" ]
then
    vlog "Rescheduling exec jobs $execjobs"
    $SGE_ROOT/bin/$ARCH/qmod -rj $execjobs
fi

stagingjobs=`$SGE_ROOT/bin/$ARCH/qstat -q $stagingsubq@$myhostname -u '*' | perl -ne 's/^\s+//;print' | cut -f 1 -d ' ' | perl -ne 'chomp;if(/(\d+)/){print "$1 "}'`
if [ "$stagingjobs" != "" ]
then
    vlog "Rescheduling staging jobs $stagingjobs"
    $SGE_ROOT/bin/$ARCH/qmod -rj $stagingjobs
fi

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
	runningjobs=`$SGE_ROOT/bin/$ARCH/qstat -j $job | grep sge_o_host | grep $myhostname`
	if [ "$runningjobs" != "" ]
	    echo "Job $job submitted from $myhostname is still running"
	    isrunning=1
	fi
    done
    
    if [ $isrunning == 1 ]
    then
	vlog "Jobs still running from this submit host"
    else
	jobs1=`$SGE_ROOT/bin/$ARCH/qstat -q $execq@$myhostname -u '*'`
	jobs2=`$SGE_ROOT/bin/$ARCH/qstat -q $stagingsubq@$myhostname -u '*'`
	if [ "$jobs1" == "" ] && [ "$jobs2" == "" ] 
	then
	    break;
	fi
    fi
    i=`expr $i + 1`
    sleep 6
done

##
#Clean up SGE. Removing myself from queues
sgemaster=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $myhostname $stagingsubq
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $myhostname $execq
$SGE_ROOT/bin/$ARCH/qconf -de $myhostname
$SGE_ROOT/bin/$ARCH/qconf -ds $myhostname
$SGE_ROOT/bin/$ARCH/qconf -kej $myhostname
$SGE_ROOT/bin/$ARCH/qconf -dh $myhostname

#if -kej failed try again
myhostnameshort=`hostname`
if [ -s $SGE_ROOT/default/spool/$myhostnameshort/execd.pid ]
then
        echo "qconf -kej appears to have failed. Checking $SGE_ROOT/default/spool/$myhostnameshort/execd.pid"
        execpid=`cat $SGE_ROOT/default/spool/$myhostnameshort/execd.pid`
        echo "Killing $execpid"
        kill $execpid
fi

##
#Zero out sgemaster preventing further use of SGE on this node
echo "" > $SGE_ROOT/$SGE_CELL/common/act_qmaster
echo "OFFLINE" > $vappio_runtime/node_type

