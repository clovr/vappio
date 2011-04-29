vappio_scripts=/opt/vappio-scripts
vappio_userdata=/mnt/
vappio_runtime=/var/vappio/runtime/
user_data_scripts=/mnt/user-scripts

#Use of vappio_log is deprecated
vappio_log=/tmp/vappio.log
#Set default to report logs through rsyslogd
if [ "$mirrorlogs" = "" ]
then
    mirrorlogs=0
fi
##
#Debugging and error reporting functions
#Report errors to the error log
vlogmirror() {
 npipe=/tmp/$$.tmp
 npipe2=/tmp/$$e.tmp
 if [ ! -e "$npipe" ] && [ ! -e "$npipe2" ]
 then
     trap "rm -f $npipe $npipe2" EXIT
     mknod $npipe p || true
     mknod $npipe2 p || true
     tee <$npipe >(/usr/bin/logger -p local0.info -t VP.$0 --) &
     tee <$npipe2 >(/usr/bin/logger -p local0.warning -t VP.$0 --) 1>&2 &
     exec 1>$npipe
     exec 2>$npipe2
 fi
}

if [ "$mirrorlogs" = 1 ] && [ -z "$PS1" ]
then
    vlogmirror
fi

vlog() { 
    if [ "$2" != "" ]
    then
	pri="$2"
    else
	pri="info"
    fi
    echo $1 | /usr/bin/logger -p local0.$pri -t VP --;
}

#Report an error back to the master nodes
#Simplies debugging by keeping all error messages in one spot
if [ -f "$vappio_log" ]
then
    logcount=`wc -l < $vappio_log`
fi

verror() { 
    if [ -z "$PS1" ]
    then
	vlogmirror
    fi
    vlog "ERROR LOGGED: $1" error
    #msg=$1
    #master_node=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
    #if [ "$master_node" != "" ]
    #then
#	stamp=`date +'%T %D'`
#	myhostname=`hostname -f`
    #Get latest log messages
#	newlogcount=`wc -l < $vappio_log`
#	newloglines=`expr $newlogcount - $logcount`
#	logmsg=`tail -n $newloglines $vappio_log`
#	reportstr=`echo -e "[$myhostname $stamp]\n$msg\n$logmsg"`
#	errorfile=`curl --retry 2 --silent --show-error --fail -d "msg=$reportstr" "http://$master_node:8080/announce.cgi"`
#       vlog "ERROR LOGGED: $1"
#    fi
}

# This is used to make changes to the configuration at boot time
mod_config() { perl -pi -e "s/^$1=.*/$1=$2/" $vappio_scripts/vappio_config.sh; }

#Data transfer function 
#Arguments are file source and destination that are passed through to rsync
#eg. vcopy (--delete $staging_dir/ root@$remotehost:$staging_dir)
#eg. vcopy ($staging_dir/ root@$remotehost:$staging_dir)
#eg. vcopy (-R $f root@$remotehost:/)
vcopy() {
    vlog "CMD: rsync -av -R -O -e \"$ssh_client -i $ssh_key $ssh_options\" @"
    rsync -av -R -O -e "$ssh_client -i $ssh_key $ssh_options"  @
}

vnetstatus() {
    ipaddr=""
    timeout=60
    i=0
    ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`
    while [ "$ipaddr" = "" ] && [ $i -lt $timeout ]
    do
	ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`
	sleep 1
	echo -n "."
	i=`expr $i + 1`
    done
}

vnodestatus() {
    if [ -f "$vappio_runtime/node_type" ]
    then
	nodetype=`cat $vappio_runtime/node_type`
    fi
    hostn=`hostname`
    timeout=60
    i=0
    while ( [ "$nodetype" = 'OFFLINE' ] || [ "$nodetype" = 'PENDING' ] || [ "$nodetype" = "" ] || [ "$hostn" = "(none)" ] ) && [ $i -lt $timeout ]
    do
	echo -n '.'
	if [ -f "$vappio_runtime/node_type" ]
	then
	    nodetype=`cat $vappio_runtime/node_type`
	fi
	sleep 1
	hostn=`hostname`
	i=`expr $i + 1`
    done 
}

export BASH_ENV=
export HISTFILE=

##SGE CONFIG
export SGE_ROOT=/var/lib/gridengine
export SGE_CELL=default
export ARCH=lx26-ia64
export SGE_ARCH=lx26-ia64

sge_exec_user=www-data
sgeadmin_user=sgeadmin
apache_user=www-data # www-data under Ubuntu, apache is also common
sge_project=$vappio_scripts/sge/global.project

#SGE queues
global_conf=$vappio_scripts/sge/global
sched_conf=$vappio_scripts/sge/ge_sched.conf
execq_conf=$vappio_scripts/sge/exec.q
pipelineq_conf=$vappio_scripts/sge/pipeline.q
pipelinewrapperq_conf=$vappio_scripts/sge/pipelinewrapper.q
harvestingq_conf=$vappio_scripts/sge/harvesting.q
stagingq_conf=$vappio_scripts/sge/staging.q
stagingsubq_conf=$vappio_scripts/sge/stagingsub.q
wfq_conf=$vappio_scripts/sge/wf.q
repositoryq_conf=$vappio_scripts/sge/repository.q
execq=exec.q
execslots=2
masterslots=1

##Time in minutes prior to hourly rollover since launch to start activity checks
rolloverstart=10
##Time in minutes to poll activity before automatic shutdown
idleshutdown=3
##Time in minutes to delay before shutdown
delayshutdown=1
#Number of 10-second intervals to wait for master node to boot
waitformastertimeout=50
#Delay boot until configuration is complete
waitonboot=y

##Workflow 
wfworking_dir=/mnt/wf-working
scratch_dir=/mnt/scratch

##SSH KEY CONFIG
#ssh_key=/home/guest/.ssh/guest
keys_dir=/mnt/keys
ssh_key=/mnt/keys/devel1.pem
#ssh-hpn is high performance ssh
#ssh_client=/usr/local/bin/ssh-hpn
ssh_client=/usr/bin/ssh
#turn off ssh encryption for faster transfer on trusted networks
ssh_options="-q -oNoneSwitch=yes -oNoneEnabled=yes -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null"

# VAPPIO SETUP
default_node_type=master
default_master_node=localhost
user_data_file=/mnt/user-data.txt


##Data placement config
vappio_data_placement=1
##Staging
#Dedicated queue for data staging
stagingq=staging.q
stagingslots=2
#Secondary queue for data staging
stagingsubq=stagingsub.q
stagingsubslots=1
#Dedicated queue for syncing wf XML
wfq=wf.q

pipelineq=pipeline.q
pipelinewrapperq=pipelinewrapper.q

staging_script=$vappio_scripts/staging.sh
seeding_script=$vappio_scripts/seeding.sh
stagingwf_script=$vappio_scripts/stagingwf.sh

#Size cutoffs for transfer with fast file transfer method, eg gridftp
largefilesize=1MB # 1MB
transfer_method=rsync #gridftp #rsync or gridftp

staging_dir=/mnt/staging
#update grid job status after job starts running
#otherwise jobs remain in pending state until completion
#results in additional connections to master
#set to 'n' to reduce load on master when starting jobs 
updatestatus=y

##Harvesting config
harvestingq=harvesting.q
harvestingslots=2
harvesting_dir=/mnt/harvesting
harvesttmp=0 #beta, harvest tmp dir to master on failures
#Dedicated queue for syncing project repositories
repositoryq=repository.q

harvesting_script=$vappio_scripts/harvesting.sh
harvestingwf_script=$vappio_scripts/harvestingwf.sh

#if 'y', retreive all output before marking a job complete
#if 'n', the workflow will continue after a distributed job and harvesting will run concurrently in the background
waitonharvest=y

#Boot flags stored in a mounted area can change behavior at boot time. The flags are simply files and can be created with touch
#Supported flags (all optional)
#$vappio_bootflags/skip_vmwarestartnodes  - bypass setup_node.sh and start_master.sh when under vmware
vappio_bootflagsdir=/mnt/config

if [ -f /opt/vappio-scripts/clovrEnv.sh ]
then
    source /opt/vappio-scripts/clovrEnv.sh
fi