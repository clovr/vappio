#!/bin/bash
#stop_master.sh
#Stops a vappio master node

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# Force remove all running jobs
$SGE_ROOT/utilbin/$ARCH/qdel -f -u '*'

#TODO, should probably wait here for all jobs to finish
sleep 5

# Remove all hosts and queues
$vappio_scripts/sge/wipe_queues.sh

rm -f $vappio_runtime/syncinprogress
#Stop execd
#if -kej failed try again
myhostnameshort=`hostname`
/etc/init.d/gridengine-exec stop
if [ -s /var/run/gridengine-execd.pid ]
then
    echo "qconf -kej appears to have failed. Checking $SGE_ROOT/default/spool/$myhostnameshort/execd.pid"
    execpid=`cat $SGE_ROOT/default/spool/$myhostnameshort/execd.pid`
    echo "Killing $execpid"
    kill $execpid
fi
kill `ps h -C sge_execd -o pid`

/etc/init.d/gridengine-master stop

echo "" > $SGE_ROOT/$SGE_CELL/common/act_qmaster

##
# Cleaning up some files specific to the master
rm -f $SGE_ROOT/default/spool/qmaster/messages

echo "OFFLINE" > $vappio_runtime/node_type
date > $vappio_runtime/last_stop_master
