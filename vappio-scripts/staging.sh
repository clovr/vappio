#!/bin/sh
#Mirrors staging directory from the MASTER or DATA_NODE to an EXEC_NODE
#
#In the case where an EXEC_NODE is already staged, it can stage other nodes
#in a peer-to-peer manner. This is achieved through the stagingsub.q
#
#Invoked by workflow start, start_exec, and SGE prolog for the exec.q. 
#
#Scheduled through SGE running from staging.q(MASTER_NODE,DATA_NODE),stagingsub.q(EXEC_NODE).
#Note, the rsync is invoked so that the MASTER,DATA pushes data to the EXEC_NODE
#This allows for coordination of staging so that a configurable number of staging steps
#run concurrently as determined by the number of slots in the staging.q.

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###" 
vlog "### $0 (`whoami`) on `hostname`" 
vlog "###" 

#The remotehost has been sucessfully staged 
#and is ready to seed peers
remotehost="$1"

if [ -f $vappio_runtime/no_dns ]
then
    ping $remotehost -c 1
    if [ $? == 0 ]
    then
	vlog "ping succeeded to $remotehost. assuming hostname"
    else
	vlog "ping failed to $remotehost"
	vlog "attempting to derive IP address"
	o1='1[0-9]{0,2}|2([6-9]|[0-4][0-9]?|5[0-4]?)?|[3-9][0-9]?'
	o0='0|255|'"$o1"
	if echo "$remotehost" | egrep -v "^($o1)(\.($o0)){2}\.($o1)$" 
	then
	    remotehostipaddr=`echo $remotehost | perl -ne '/^\w+\-([\d\-]+)/;$x=$1;$x =~ s/\-/\./g;print $x'`
	    vlog "parsed ip address $remotehostipaddr from $remotehost"
	#we have the IP
	    ping $remotehostipaddr -c 1
	    if [ $? == 0 ]
	    then	    
		echo "$remotehostipaddr $remotehost $remotehost" >> /etc/hosts
	    else
		vlog "ERROR. Invalid ip ($remotehostipaddr) from host $remotehost"
		exit 1;
	    fi
	else
	    vlog "ping $remotehost failed and unable to parse ip address from $remotehost"
	#fail
	    exit 1;
	fi
    fi
fi
#copy staging area
vlog "Start staging from $staging_dir/ to $remotehost:$staging_dir"
vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" --delete $staging_dir/ root@$remotehost:$staging_dir"
rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --delete $staging_dir/ root@$remotehost:$staging_dir 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value $1"
    verror "STAGING FAILURE";
    exit 1;
fi

