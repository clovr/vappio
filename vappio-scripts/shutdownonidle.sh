#!/bin/bash

#shutdownonidle.sh
#Checks if a node is performing any work and if not schedules a shutdown in 5 minutes
#Shutdown can be forced by adding a file
#touch /var/vappio/runtime/forceautoshutdown
#Shutdown can be disabled by adding a file
#touch /var/vappio/runtime/noautoshutdown
#Auto shutdown can be disabled for an entire cluter by running placing a file on the master web htdocs
#touch /var/www/noautoshutdown

vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh


#Support for manual override, cluster wide
myhostname=`hostname -f`
master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
/usr/bin/curl -f -s http://$master/noautoshutdown
if [ $? = 0 ] || [ -f "$vappio_runtime/noautoshutdown" ]
then
    vlog "SKIPPING AUTOSHUTDOWN. MANUAL OVERRIDE"
    exit 0
fi

nodetype=`cat $vappio_runtime/node_type`

#Don't shutdown master unless force
if [ $nodetype != "master" ] || [ -f "$vappio_runtime/forceautoshutdown" ]
    #Check for jobs running on this host
    $SGE_ROOT/bin/$ARCH/qstat -u '*' -l hostname=$myhostname > $vappio_runtime/sge.running 
    #Check for staging,harvesting jobs or other jobs submitted by this host
    $SGE_ROOT/bin/$ARCH/qstat | grep sge_o_host | grep $myhostname >> $vappio_runtime/sge.running 
    #Check for hadoop jobs
    /opt/hadoop/bin/hadoop job -list | grep running | /usr/bin/perl -ne '($num) = ($_ =~ /(\d+) jobs /);print $_ if($num>0);'>> $vappio_runtime/sge.running 

    if [ -s $vappio_runtime/sge.running ]
    then
	echo "Active jobs on $myhostname, aborting shutdown"
	cat $vappio_runtime/sge.running
	exit 0
    fi
    #Keep checking over an interval, $idleshutdown from vappio_config.sh
    i=0
    while [ "$i" -le "$idleshutdown" ]
    do 
    #Add additional checks here
	echo "Querying for idle stat at $i minutes"
    #Check for jobs running on this host
	$SGE_ROOT/bin/$ARCH/qstat -u '*' -l hostname=$myhostname >> $vappio_runtime/sge.running 
    #Check for staging,harvesting jobs or other jobs submitted by this host
	$SGE_ROOT/bin/$ARCH/qstat | grep sge_o_host | grep $myhostname >> $vappio_runtime/sge.running 
    #Check for hadoop jobs
	/opt/hadoop/bin/hadoop job -list | grep running | /usr/bin/perl -ne '($num) = ($_ =~ /(\d+) jobs /);print $_ if($num>0);' >> $vappio_runtime/sge.running 
    #Shortcircuit if any running jobs
	if [ -s $vappio_runtime/sge.running ]
	then
	    echo "Active jobs on $myhostname, aborting shutdown"
	    cat $vappio_runtime/sge.running
	    exit 0
	fi
	sleep 60 
	i=`expr $i + 1`
    done
    #If non empty file then short circuit shutdown
    if [ -s $vappio_runtime/sge.running ]
    then
        echo "Active jobs on $myhostname, aborting shutdown"
	cat $vappio_runtime/sge.running	
	exit 0
    fi
then
    echo "Detected node_type:$nodetype. Aborting shutdown"
    exit 0
fi

vlog "Scheduling forced shutdown"
if [ "$nodetype" = "exec" ]
then
    $vappio_scripts/remove_sgehost.sh $myhostname
fi

#Cancel spot instance requests for this host
master=`cat /var/lib/gridengine/default/common/act_qmaster`
myinstanceid=`curl http://169.254.169.254/latest/meta-data/instance-id`
$ssh_client -i $ssh_key $ssh_options root@$master "export JAVA_HOME=/usr/lib/jvm/java-6-openjdk/;export EC2_HOME=/opt/ec2-api-tools-1.3;/opt/ec2-api-tools-1.3/bin/ec2-describe-spot-instance-requests -K /tmp/local_key.pem -C /tmp/local_cert.pem | grep $myinstanceid | cut -f 2 | xargs /opt/ec2-api-tools-1.3/bin/ec2-cancel-spot-instance-requests -K /tmp/local_key.pem -C /tmp/local_cert.pem"

if [ "$nodetype" = "master" ]
then
    vp-terminate-cluster --name=local
else
    vp-terminate-instances --by=$myhostname
fi

verror "Scheduling shutdown in $delayshutdown minutes of $myhostname"
/sbin/shutdown -h +$delayshutdown "Cron enabled shutdown scheduled. Override by running 'shutdown -c'" 
