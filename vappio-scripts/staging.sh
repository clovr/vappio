#!/bin/bash
#staging.sh $remotehostname [$file1 $file2 $directory1 $directory2... ]

#Mirrors staging directory from the MASTER or DATA_NODE to an
#EXEC_NODE named $remotehostname. Default option is to mirror the
#configured staging directory. A second argument can specify a list of
#files or directories to stage. Absolute paths should be used. If
#files or directories are specified, they should be absolute paths and
#formatted as expected by rsync.

#In the case where an EXEC_NODE is already staged, it can stage other
#nodes in a peer-to-peer manner. This is achieved through the
#stagingsub.q

#This script is invoked by workflow start, start_exec, and SGE prolog for the
#exec.q.

#Scheduled through SGE running from staging.q(MASTER_NODE,DATA_NODE),
#stagingsub.q(EXEC_NODE).  Note, the rsync is invoked so that the
#MASTER,DATA pushes data to the EXEC_NODE. This allows for coordination
#of staging so that a configurable number of staging steps run
#concurrently as determined by the number of slots in the staging.q.

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
shift

if [ -f $vappio_runtime/no_dns ]
then
    #TODO move this code into a function
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
#If argument is specified
#copy specified files
if [ "$1" != "" ]
then
    while (( "$#" )); do
	if [ -d "$1" ]
	then
	    vlog "Start staging of directory $1 to $remotehost:$1"
	    vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" --delete $1 root@$remotehost:/"
	    rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --delete $1 root@$remotehost:/ 1>> $vappio_log 2>> $vappio_log
	else
	    vlog "Start staging of file $1 to $remotehost:$1"
	    vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" $1 root@$remotehost:$1"
	    rsync -av -e "$ssh_client -i $ssh_key $ssh_options" $1 root@$remotehost:$1 1>> $vappio_log 2>> $vappio_log
	fi
	if [ $? == 0 ]
	then
	    vlog "rsync success. return value: $?"
	else
	    vlog "ERROR: $0 rsync fail. return value $?"
	    verror "STAGING FAILURE";
	exit 1;
	fi
	shift
    done
else
#copy staging area
    vlog "Start staging from $staging_dir/ to $remotehost:$staging_dir"
    if [ "$transfer_method" == "gridftp" ]
	then
        #This method transfers files > $largefilesize with gridftp
        #These files are "synced" based on size only, datestamps are ignored
        #First list only large files and print out list for gridftp
	vlog "CMD:rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" --min-size $largefilesize --itemize-changes -n --delete $staging_dir/ root@$remotehost:$staging_dir 2>> $vappio_log | grep \"<f\" | perl -e 'while(<STDIN>){chomp;split(/\s+/);print \"file://$ARGV[1]/$_[1] ftp://$ARGV[0]:5000/$ARGV[1]/$_[1]\n\"}' > /tmp/$$.gridftp.staging.list"
	rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --min-size $largefilesize --size-only --itemize-changes -n --delete $staging_dir/ root@$remotehost:$staging_dir 2>> $vappio_log | grep "<f" | perl -e 'while(<STDIN>){chomp;split(/\s+/);print "file://$ARGV[1]/$_[1] ftp://$ARGV[0]:5000/$ARGV[1]/$_[1]\n"}' $remotehost $staging_dir > /tmp/$$.gridftp.staging.list
	if [ $? == 0 ]
	    then
	    vlog "rsync success. return value: $?"
	else
	    vlog "ERROR: $0 rsync fail. return value $?"
	    verror "LIST LARGEFILE STAGING FAILURE";
	    exit 1;
	fi
        #First set up all directories on the receiving side
        #vlog "CMD: rsync --dirs -lptgoD -e \"$ssh_client -i $ssh_key $ssh_options\" $staging_dir/ root@$remotehost:$staging_dir"
        #rsync --dirs -lptgoD -e "$ssh_client -i $ssh_key $ssh_options" $staging_dir/ root@$remotehost:$staging_dir
        #Do gridftp of large files
	if [ -s "/tmp/$$.gridftp.staging.list" ]
	    then
	    export GLOBUS_LOCATION=/opt/globus-5.0.0
	    source $GLOBUS_LOCATION/etc/globus-user-env.sh
	    export LD_LIBRARY_PATH=/opt/globus-5.0.0/lib
  	    #Can't get udt to work yet
	    #/opt/globus-5.0.0/bin/globus-url-copy -udt -p 8 -vb -cd -f /tmp/$$.gridftp.staging.list 1>> $vappio_log 2>> $vappio_log 
	    #/opt/globus-5.0.0/bin/globus-url-copy -tcp-bs 1MB -p 8 -vb -cd -f /tmp/$$.gridftp.staging.list 1>> $vappio_log 2>> $vappio_log 
	    #/opt/globus-5.0.0/bin/globus-url-copy -tcp-bs 17500 -p 8 -vb -cd -f /tmp/$$.gridftp.staging.list 1>> $vappio_log 2>> $vappio_log 
	    /opt/globus-5.0.0/bin/globus-url-copy -p 8 -vb -cd -pp -f /tmp/$$.gridftp.staging.list 1>> $vappio_log 2>> $vappio_log 
	    if [ $? == 0 ]
		then
		vlog "gridftp success. return value: $?"
	    else
		vlog "ERROR: $0 gridftp fail. return value $?"
		verror "STAGING FAILURE GRIDFTP";
		exit 1;
	    fi
	fi
        #Want to update permissions but avoid second copy, need --size-only because globus-url-copy does not preserve time
        #The rest through rsync: smaller files, delete, and reset permissions etc
        #vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" --delete $staging_dir/ root@$remotehost:$staging_dir"
	rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --itemize-changes --max-size $largefilesize --temp-dir $scratch_dir --delete $staging_dir/ root@$remotehost:$staging_dir 1>> $vappio_log 2>> $vappio_log
	if [ $? == 0 ]
	    then
	    vlog "rsync success. return value: $?"
	else
	    vlog "ERROR: $0 rsync fail. return value $?"
	    verror "STAGING FAILURE";
	    exit 1;
	fi
    else
    #Plain ole' rsync
	vlog "CMD: rsync -av -e \"$ssh_client -i $ssh_key $ssh_options\" --temp-dir $scratch_dir --delete $staging_dir/ root@$remotehost:$staging_dir"
	rsync -av -e "$ssh_client -i $ssh_key $ssh_options" --delete $staging_dir/ root@$remotehost:$staging_dir 1>> $vappio_log 2>> $vappio_log
	if [ $? == 0 ]
	    then
	    vlog "rsync success. return value: $?"
	else
	    vlog "ERROR: $0 rsync fail. return value $?"
	    verror "STAGING FAILURE";
	    exit 1;
	fi
    fi
fi

