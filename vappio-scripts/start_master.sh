#!/bin/bash
#start_master.sh
#Starts a Vappio master host

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# start_master.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

#stop node if already running
$vappio_scripts/stop_node.sh

#conf sgemaster
myhostname=`vhostname`
echo "$myhostname" > $SGE_ROOT/$SGE_CELL/common/act_qmaster

/etc/init.d/gridengine-master restart
sleep 3
echo "Started master"

# add an administrative host
qconf -ah $myhostname 

# Remove all hosts and queues from a pre-existing save (task #100)
# Goes here because it kills sgeexecd
$vappio_scripts/sge/wipe_queues.sh

/etc/init.d/gridengine-exec start

# add user to operator list
qconf -ao $sge_exec_user
# add user to manager list
qconf -am $sge_exec_user
# add apache user to manager list
qconf -am $apache_user
# add a submit host
qconf -as $myhostname
# add project from file
qconf -Aprj $sge_project

#output of qconf -sconf
$SGE_ROOT/bin/$ARCH/qconf -Mconf $global_conf
#output of qconf -ssconf
$SGE_ROOT/bin/$ARCH/qconf -Msconf $sched_conf

## add a queue from file
$SGE_ROOT/bin/$ARCH/qconf -Aq $execq_conf
$SGE_ROOT/bin/$ARCH/qconf -Aq $pipelineq_conf
$SGE_ROOT/bin/$ARCH/qconf -Aq $pipelinewrapperq_conf
$SGE_ROOT/bin/$ARCH/qconf -Aq $stagingq_conf 
$SGE_ROOT/bin/$ARCH/qconf -Aq $stagingsubq_conf 
$SGE_ROOT/bin/$ARCH/qconf -Aq $wfq_conf 
$SGE_ROOT/bin/$ARCH/qconf -Aq $harvestingq_conf
$SGE_ROOT/bin/$ARCH/qconf -Aq $repositoryq_conf
# add to a list attribute of an object
# -aattr obj_nm attr_nm val obj_id_lst
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $stagingq 
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $stagingsubq 
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $wfq 
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $repositoryq 
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $harvestingq 
#$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $execq
$SGE_ROOT/bin/$ARCH/qconf -aattr queue slots $stagingslots $stagingq
$SGE_ROOT/bin/$ARCH/qconf -aattr queue slots $stagingsubslots $stagingsubq
$SGE_ROOT/bin/$ARCH/qconf -aattr queue slots $harvestingslots $harvestingq
$SGE_ROOT/bin/$ARCH/qconf -aattr queue slots $execslots $execq

#Limit slots to 1 on the master
#Can also set to zero (slots=0) to "hold" work in the exec.q until
#there are additional hosts
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $execq
#This will prevent more than 1 job from running across any queue
#$SGE_ROOT/bin/$ARCH/qconf -mattr exechost complex_values slots=1 $myhostname
cloud_type=`cat /var/vappio/runtime/cloud_type`
#Set local vm to numcpus for local VMs
numcpus=`cat /proc/cpuinfo | grep -c '^processor'`
if [ "$cloud_type" == "vbox" ] || [ "$cloud_type" == "vmware" ] || [ -e /var/vappio/runtime/cloudonlymode ]
then
    $SGE_ROOT/bin/$ARCH/qconf -rattr queue slots $numcpus $execq@$myhostname

    # If we are running cloud-only mode we will also want to bump up the number of concurrent pipelines 
    # that we can run
    if [ -e /var/vappio/runtime/cloudonlymode ]
    then
        pipelineslots=`python -c "print '%d' % round($numcpus / 2.0)"`
	    $SGE_ROOT/bin/$ARCH/qconf -rattr queue slots $pipelineslots $pipelineq@$myhostname
    fi

else
    if [ "$cloud_type" == "diag" ]
    then
	#Limit master load on DIAG machines
	$SGE_ROOT/bin/$ARCH/qconf -aattr queue load_thresholds np_load_avg=1 $execq@$myhostname
    else
	$SGE_ROOT/bin/$ARCH/qconf -rattr queue slots $masterslots $execq@$myhostname
    fi

fi

$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $pipelineq
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $pipelinewrapperq

