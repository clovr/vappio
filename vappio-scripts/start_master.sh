#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# start_master.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

# create local directories for workflows
$vappio_scripts/prep_directories.sh

# CURRENTLY DISABLED
#put ssh key in expected place for remote logins
chmod 600 /mnt/devel1.pem
#should be changed to sge user
chown $apache_user:$apache_user /mnt/devel1.pem

#conf sgemaster
myhostname=`hostname -f`
echo "$myhostname" > $SGE_ROOT/$SGE_CELL/common/act_qmaster
#remove local execd spool dir
rm -rf /var/spool/sge
mkdir /var/spool/sge
chown $sgeadmin_user:$sgeadmin_user /var/spool/sge

#/etc/init.d/sgemaster start
$SGE_ROOT/$SGE_CELL/common/sgemaster

# Remove all hosts and queues from a pre-existing save (task #100)
# Goes here because it kills sgeexecd
$vappio_scripts/sge/wipe_queues.sh

$SGE_ROOT/$SGE_CELL/common/sgeexecd

# add user to operator list
$SGE_ROOT/bin/$ARCH/qconf -ao $sge_exec_user
# add user to manager list
$SGE_ROOT/bin/$ARCH/qconf -am $sge_exec_user
# add apache user to manager list
$SGE_ROOT/bin/$ARCH/qconf -am $apache_user
# add an administrative host
$SGE_ROOT/bin/$ARCH/qconf -ah $myhostname 
# add a submit host
$SGE_ROOT/bin/$ARCH/qconf -as $myhostname
# add project from file
$SGE_ROOT/bin/$ARCH/qconf -Aprj $sge_project
## add a queue from file
$SGE_ROOT/bin/$ARCH/qconf -Aq $execq_conf
$SGE_ROOT/bin/$ARCH/qconf -Aq $pipelineq_conf
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

$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $pipelineq

# CURRENTLY DISABLED
#Temp to set up staging and test project
#Should pull staing from S3
#cp /root/staging.tgz $staging_dir
#pushd $staging_dir
#tar xvzf staging.tgz
#popd
#cp /root/testproject.tgz $harvesting_dir
#pushd $harvesting_dir
#tar xvzf testproject.tgz
#popd

echo "MASTER_NODE" > $vappio_runtime/node_type

