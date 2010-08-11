#/bin/bash
# Expected to be run as
# start_exec.sh $MASTER_NODE
USAGE="USAGE:$0 <master_node hostname or IP>\n
Enter a valid hostname of a master node\n
If you are running a CloVR VMware cluster with no DNS,\n
you can also enter the IP address of a master node.\n
If no hostname is provided, the script will attempt to\n
read from $vappio_userdata/master_node";

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

if [ "$1" != "" ]
then
    MASTER_NODE=$1
else
    MASTER_NODE=`cat $vappio_userdata/master_node`
fi

#capture time
min=`date +"%-M"`

if [ "$MASTER_NODE" == "" ]
then 
    echo -e $USAGE
    exit 1;
else
    ping $MASTER_NODE -c 1 
    if [ $? == 0 ]
    then
	echo "Master node $MASTER_NODE found. Attempting to add this node to the cluster"
    else
	#Keep checking over an interval, sleep on each iteration
	#$waitformaster defined in vappio_config.sh
	i=0
	while [ "$i" -le "$waitformastertimeout" ]
	  do 
	  ping $MASTER_NODE -c 1
	  if [ $? == 0 ]
	      then
	      echo "Master node $MASTER_NODE found. Attempting to add this node to the cluster"
	      break;
	  else
	      echo "Master node $MASTER_NODE not found. Sleeping"
	      i=`expr $i + 1`
	      sleep 10
	  fi
	done
    fi
fi

#stop node if already running
$vappio_scripts/stop_node.sh

# create local directories for workflows
$vappio_scripts/prep_directories.sh

#conf sgemaster
echo $MASTER_NODE > $SGE_ROOT/$SGE_CELL/common/act_qmaster

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
	curl --retry 5 --silent --show-error --fail "http://$MASTER_NODE:8080/vappio/addHost_ws.py?host=$myhostname"
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
	curl --retry 5 --silent --show-error --fail "http://$MASTER_NODE:8080/vappio/addHost_ws.py?host=$myhostname&ipaddr=$ipaddr"
    fi
else
    curl --retry 5 --silent --show-error --fail "http://$MASTER_NODE:8080/vappio/addHost_ws.py?host=$myhostname"
fi

sgemaster=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`

#start execd
/etc/init.d/gridengine-exec start

#add as submit host , needed to submit to staging q
$SGE_ROOT/bin/$ARCH/qconf -as $myhostname

# Stage data from the staging area
# Accept data from nodes in either the staging or stagingsub queues
# On completion, add this host to the stagingsub queue so that it can stage other hosts
# This is a blocking call, so that the node does not come "online" until staging completes
# Currently makes 2 attempts at staging
qsubcmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -b y -sync y -q $stagingq,$stagingsubq $seeding_script $myhostname $stagingsubq"
vlog "Running $qsubcmd"
$qsubcmd 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    echo "Successfully seeded node $myhostname"
else
    echo "ERROR: Failed to seed node $myhostname. See error log /mnt/scratch. Retrying"
    qsubcmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -b y -sync y -q $stagingq,$stagingsubq $seeding_script $myhostname $stagingsubq"
    vlog "Running $qsubcmd"
    $qsubcmd 1>> $vappio_log 2>> $vappio_log
    if [ $? == 0 ]
    then
	echo "Successfully seeded node $myhostname on second try"
    else
	echo "ERROR: Failed to seed node $myhostname on second try. See error log /mnt/scratch. Exiting boot process prematurely"
	exit 1;
    fi
fi

#add to runnable hosts in $execq
$SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $myhostname $execq 
#set slots to number of CPUs
numcpus=`cat /proc/cpuinfo | grep -c CPU`
$SGE_ROOT/bin/$ARCH/qconf -rattr queue slots $numcpus $execq@$myhostname

echo "EXEC_NODE" > $vappio_runtime/node_type

##
#For EC2 only, add autoshutdown cron for exec node types
#add cron job to shutdown at 60 mins if idle
cloudtype=`cat $vappio_runtime/cloud_type`
if [ "$cloudtype" == "EC2" ]
then
    #Set EC2 host group
    instancetype=`curl -f -s http://169.254.169.254/1.0/meta-data/instance-type`
    #Add to host group
    shutdownmin=$(($min-$rolloverstart))
    if [ $shutdownmin -lt 0 ]
    then
	shutdownmin=$((60 + $shutdownmin));
    fi
    echo "$shutdownmin * * * * $vappio_scripts/amazonec2/shutdownonidle.sh" > $vappio_runtime/shutdown.crontab
    crontab -u root $vappio_runtime/shutdown.crontab
fi
