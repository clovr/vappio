#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# Expected to be run as
# start_exec.sh $MASTER_NODE
USAGE="USAGE:$0 <master_node hostname or IP>\n
Enter a valid hostname of a master node\n
If you are running a CloVR VMware cluster with no DNS,\n
you can also enter the IP address of a master node"

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

MASTER_NODE=$1

if [ "$MASTER_NODE" == "" ]
then 
    echo -e $USAGE
#    echo "USAGE:$0 <master_node hostname or IP>"
#    echo "Enter a valid hostname of a master node";
#    echo "If you are running a CloVR VMware cluster with no DNS, you can also enter the IP address of a master node"
    exit;
else
    ping $MASTER_NODE -c 1
    if [ $? == 0 ]
    then
	echo "Master node $MASTER_NODE found. Adding this node to the cluster"
    else
	echo "ERROR Master node $MASTER_NODE not found."
	echo -e $USAGE
	exit;
    fi
fi

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

#start sgeexecd here or after add_host?
myhostname=`hostname -f`

#add this host as an administrative host
#if there is no DNS, we need to add master to our hosts file
#and master will add us 
if [ -f $vappio_runtime/no_dns ]
then
    #should check here that $MASTER_NODE is an ipddr
    masterip=$MASTER_NODE
    o1='1[0-9]{0,2}|2([6-9]|[0-4][0-9]?|5[0-4]?)?|[3-9][0-9]?'
    o0='0|255|'"$o1"
    if echo "$masterip" | egrep -v "^($o1)(\.($o0)){2}\.($o1)$" >/dev/null; then
	echo "valid hostname $MASTER_NODE"
	#parse IP
	curl --retry 5 --silent --show-error --fail "http://$MASTER_NODE:8080/add_host.cgi?host=$myhostname"
    else
	MASTER_NODE=`echo $masterip | sed 's/\./\-/g'`
	MASTER_NODE="clovr-$MASTER_NODE"
	echo "Found $masterip, assuming hostname $MASTER_NODE"
	if grep $masterip /etc/hosts ; then
	    echo "hostname already found, skipping"
	else
	    echo "$masterip $MASTER_NODE $MASTER_NODE" >> /etc/hosts
	fi
	echo $MASTER_NODE > $SGE_ROOT/$SGE_CELL/common/act_qmaster
	ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`
	curl --retry 5 --silent --show-error --fail "http://$MASTER_NODE:8080/add_host.cgi?host=$myhostname&ipaddr=$ipaddr"
    fi
fi

sgemaster=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`

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

cloudtype=`cat $vappio_runtime/cloud_type`
if [ "$cloudtype" == "EC2" ]
then
    #add autoshutdown cron for exec node types
    #add cron job to shutdown at 60 mins if idle
    min=`date +"%-M"`
    shutdownmin=$(($min-10))
    if [ $shutdownmin -lt 0 ]
    then
	shutdownmin=$((60 + $shutdownmin));
    fi
    echo "$shutdownmin * * * * $vappio_scripts/amazonec2/shutdownonidle.sh" > $vappio_runtime/shutdown.crontab
    crontab -u root $vappio_runtime/shutdown.crontab
fi
