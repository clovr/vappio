vappio_scripts=/opt/vappio-scripts
vappio_runtime=/mnt/clovr/runtime/
vappio_log=/tmp/vappio.log
vlog() { echo [`date +'%T %D'`] $1 >> $vappio_log; }

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
harvestingq_conf=$vappio_scripts/sge/harvesting.q
stagingq_conf=$vappio_scripts/sge/staging.q
stagingsubq_conf=$vappio_scripts/sge/stagingsub.q
wfq_conf=$vappio_scripts/sge/wf.q
repositoryq_conf=$vappio_scripts/sge/repository.q
execq=exec.q
execslots=1

##Workflow 
wfworking_dir=/mnt/wf-working
scratch_dir=/mnt/scratch

##SSH KEY CONFIG
#ssh_key=/home/guest/.ssh/guest
ssh_key=/mnt/devel1.pem
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

staging_script=$vappio_scripts/staging.sh
seeding_script=$vappio_scripts/seeding.sh
stagingwf_script=$vappio_scripts/stagingwf.sh

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

