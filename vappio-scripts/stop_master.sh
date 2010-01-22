#/bin/bash
#stop_master.sh
#Stops a Vappio master node

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# Force remove all running jobs
$SGE_ROOT/bin/$ARCH/qdel -f -u '*'

#Should probably wait here for all jobs to finish

# Remove all hosts and queues
$vappio_scripts/sge/wipe_queues.sh

$SGE_ROOT/$SGE_CELL/common/sgemaster stop

echo "" > $SGE_ROOT/$SGE_CELL/common/act_qmaster

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
# Cleaning up some files specific to the master
rm -f /opt/sge/default/spool/qmaster/messages

echo "OFFLINE" > $vappio_runtime/node_type
date > $vappio_runtime/last_stop_master
