#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# stop data (staging, harvesting) q
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $myhostname $harvestingq
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $myhostname $stagingq
$SGE_ROOT/bin/$ARCH/qconf -kej $myhostname
$SGE_ROOT/bin/$ARCH/qconf -ds $myhostname
$SGE_ROOT/bin/$ARCH/qconf -de $myhostname
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

echo "" > $SGE_ROOT/$SGE_CELL/common/act_qmaster
echo "OFFLINE" > $vappio_runtime/node_type

