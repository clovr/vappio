#!/bin/sh
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

#suggested improvement
#poll over 10 minute interval, if no jobs, then proceed with shutdown, provide 5 minutes notice

$SGE_ROOT/bin/$ARCH/qstat -u '*' > /tmp/sge.running

if [ -s /tmp/sge.running ]
 then
	cat /tmp/sge.running	
 else
	/sbin/shutdown -h +5 "Cron enabled shutdown scheduled. Override by running 'shutdown -c'" 
fi
