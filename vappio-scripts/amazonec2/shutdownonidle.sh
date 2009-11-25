#!/bin/sh
SGE_ROOT=/opt/sge
SGE_QMASTER_PORT=6444
SGE_EXECD_PORT=6445
export SGE_ROOT
export SGE_QMASTER_PORT
export SGE_EXECD_PORT

#suggested improvement
#poll over 10 minute interval, if no jobs, then proceed with shutdown, provide 5 minutes notice

/opt/sge/bin/lx24-x86/qstat -u guest > /tmp/sge.running

if [ -s /tmp/sge.running ]
 then
	cat /tmp/sge.running	
 else
	/sbin/shutdown -h +5 "Cron enabled shutdown scheduled. Override by running 'shutdown -c'" 
fi
