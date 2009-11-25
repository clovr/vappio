#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# Expected to be run as
# start_exec.sh $MASTER_NODE

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

MASTER_NODE=$1

# create local directories for workflows
$vappio_scripts/prep_directories.sh

# CURRENTLY DISABLED
chmod 600 /mnt/devel1.pem
#should be changed to sge user
chown $apache_user:$apache_user /mnt/devel1.pem

#conf sgemaster
echo $MASTER_NODE > $SGE_ROOT/$SGE_CELL/common/act_qmaster
#remove local execd spool dir
rm -rf /var/spool/sge
mkdir /var/spool/sge
chown $sgeadmin_user:$sgeadmin_user /var/spool/sge

#start sgeexecd
sgemaster=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
myhostname=`hostname -f`

#add this host as an administrative host
curl --retry 5 --silent --show-error --fail "http://$MASTER_NODE:8080/add_host.cgi?host=$myhostname"
#start execd
$SGE_ROOT/$SGE_CELL/common/sgeexecd

#add as submit host , needed to submit to transfer q
$SGE_ROOT/bin/$ARCH/qconf -as $myhostname

# stage the default staging data
qsubcmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -b y -sync y -q $stagingq,$stagingsubq $seeding_script $myhostname $stagingsubq"
vlog "Running $qsubcmd"
#su -p guest -c "$qsubcmd"
# Above will fail if run as guest with  error: can't chdir to /home/guest: No such file or directory"
# $SGE_ROOT/bin/$ARCH/qsub -b y -sync n -q $stagingq,$stagingsubq $seeding_script $myhostname $stagingq
$qsubcmd 1>> $vappio_log 2>> $vappio_log

#add to runnable hosts in $execq
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $execq 

echo "EXEC_NODE" > $vappio_runtime/node_type
