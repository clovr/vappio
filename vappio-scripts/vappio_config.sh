vappio_scripts=/opt/vappio-scripts
vappio_runtime=/mnt/clovr/runtime/
vappio_log=/tmp/vappio.log

##
#Debugging and error reporting functions
#Report errors to the error log
vlog() { echo [`date +'%T %D'`] $1 >> $vappio_log; }
#Report an error back to the master nodes
#Simplies debugging by keeping all error messages in one spot
if [ -f "$vappio_log" ]
then
    logcount=`wc -l < $vappio_log`
fi
verror() { 
    msg=$1
    master_node=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
    if [ "$master_node" != "" ]
    then
	stamp=`date +'%T %D'`
	myhostname=`hostname -f`
    #Get latest log messages
	newlogcount=`wc -l < $vappio_log`
	newloglines=`expr $newlogcount - $logcount`
	logmsg=`tail -n $newloglines $vappio_log`
	reportstr=`echo -e "[$myhostname $stamp]\n$msg\n$logmsg"`
	curl --retry 2 --silent --show-error --fail -d "msg=$reportstr" "http://$master_node:8080/announce.cgi"
    fi
}

# This is used to make changes to the configuration at boot time
mod_config() { perl -pi -e "s/^$1=.*/$1=$2/" $vappio_scripts/vappio_config.sh; }

export BASH_ENV=
export HISTFILE=

##SGE CONFIG
export SGE_ROOT=/opt/sge
export SGE_CELL=default
export ARCH=`$SGE_ROOT/util/arch`
sge_exec_user=guest
sgeadmin_user=sgeadmin
apache_user=www-data # www-data under Ubuntu, apache is also common
sge_project=$vappio_scripts/sge/global.project

#SGE queues
execq_conf=$vappio_scripts/sge/exec.q
pipelineq_conf=$vappio_scripts/sge/pipeline.q
harvestingq_conf=$vappio_scripts/sge/harvesting.q
stagingq_conf=$vappio_scripts/sge/staging.q
stagingsubq_conf=$vappio_scripts/sge/stagingsub.q
wfq_conf=$vappio_scripts/sge/wf.q
repositoryq_conf=$vappio_scripts/sge/repository.q
execq=exec.q
execslots=2

##Time in minutes to poll activity before automatic shutdown
idleshutdown=3
#Number of 10-second intervals to wait for master node to boot
waitformastertimeout=50

##Workflow 
wfworking_dir=/mnt/wf-working
scratch_dir=/mnt/scratch

##SSH KEY CONFIG
#ssh_key=/home/guest/.ssh/guest
ssh_key=/mnt/keys/devel1.pem
#ssh-hpn is high performance ssh
#ssh_client=/usr/local/bin/ssh-hpn
ssh_client=/usr/bin/ssh
#turn off ssh encryption for faster transfer on trusted networks
ssh_options="-oNoneSwitch=yes -oNoneEnabled=yes -oStrictHostKeyChecking=no -oUserKnownHostsFile=/dev/null"

# VAPPIO SETUP
default_master_node=localhost

##Data placement config
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

