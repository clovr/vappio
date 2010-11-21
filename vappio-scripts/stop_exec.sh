#!/bin/bash

#stop_exec.sh 
#Stops a Vappio exec host

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

myhostname=`hostname -f`

##
#Attempt to reschedule jobs and remove host
$vappio_scripts/remove_sgehost.sh $myhostname wait

#if -kej failed try again
myhostnameshort=`hostname`
if [ -s /var/run/gridengine-execd.pid ]
then
        echo "qconf -kej appears to have failed. Checking $SGE_ROOT/default/spool/$myhostnameshort/execd.pid"
        execpid=`cat $SGE_ROOT/default/spool/$myhostnameshort/execd.pid`
        echo "Killing $execpid"
        kill $execpid
fi
kill `ps h -C sge_execd -o pid`

##
#Zero out sgemaster preventing further use of SGE on this node
echo "" > $SGE_ROOT/$SGE_CELL/common/act_qmaster
echo "OFFLINE" > $vappio_runtime/node_type

