#!/bin/sh

#shutdownonidle.sh
#Checks if a node is performing any work and if not schedules a shutdown in 5 minutes

vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

myhostname=`hostname -f`

#Check for jobs running on this host
$SGE_ROOT/bin/$ARCH/qstat -u '*' -l hostname=$myhostname > $vappio_runtime/sge.running 
#Check for staging,harvesting jobs or other jobs submitted by this host
$SGE_ROOT/bin/$ARCH/qstat | grep sge_o_host | grep $myhostname >> $vappio_runtime/sge.running 

if [ -s $vappio_runtime/sge.running ]
    then
    cat $vappio_runtime/sge.running
    exit 0
fi
#Keep checking over an interval, $idleshutdown from vappio_config.sh
i=0
while [ "$i" -le "$idleshutdown" ]
do 
    #Add additional checks here
    echo "Querying for idle stat at $i minutes"
    #Check for jobs running on this host
    $SGE_ROOT/bin/$ARCH/qstat -u '*' -l hostname=$myhostname >> $vappio_runtime/sge.running 
    #Check for staging,harvesting jobs or other jobs submitted by this host
    $SGE_ROOT/bin/$ARCH/qstat | grep sge_o_host | grep $myhostname >> $vappio_runtime/sge.running 
    #Shortcircuit if any running jobs
    if [ -s $vappio_runtime/sge.running ]
	then
	cat $vappio_runtime/sge.running
	exit 0
    fi
    sleep 60 
    i=`expr $i + 1`
done

#If empty file then proceed with shutdown
if [ -s $vappio_runtime/sge.running ]
 then
	cat $vappio_runtime/sge.running	
 else
    verror "Scheduling shutdown in $delayshutdown minutes of $myhostname"
    /sbin/shutdown -h +$delayshutdown "Cron enabled shutdown scheduled. Override by running 'shutdown -c'" 
fi
