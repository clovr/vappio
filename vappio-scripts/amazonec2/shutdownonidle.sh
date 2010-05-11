#!/bin/sh
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

$SGE_ROOT/bin/$ARCH/qstat -u '*' > $vappio_runtime/sge.running

#Keep checking over an interval, $idleshutdown from vappio_config.sh
i=0
while [ "$i" -le "$idleshutdown" ]
do 
    #Add additional checks here
    echo "Querying for idle stat at $i minutes"
    $SGE_ROOT/bin/$ARCH/qstat -u '*' >> $vappio_runtime/sge.running 
    sleep 60 
    i=`expr $i + 1`
done

#If empty file then proceed with shutdown
if [ -s $vappio_runtime/sge.running ]
 then
	cat $vappio_runtime/sge.running	
 else
    myhostname=`hostname -f`
    verror("Scheduling shutdown in 5 minutes of $myhostname");
    /sbin/shutdown -h +5 "Cron enabled shutdown scheduled. Override by running 'shutdown -c'" 
fi
