#!/bin/bash
#import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# prep_directories.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

#create local directories for workflows
for i in $harvesting_dir $staging_dir $staging_dir/ergatis $wfworking_dir $scratch_dir $scratch_dir/ergatis $vappio_runtime /mnt/keys /mnt/user_data; 
do
  mkdir -p $i
  chmod 777 $i
done;

chown $sge_exec_user:$sge_exec_user $staging_dir 
chown $sge_exec_user:$sge_exec_user $wfworking_dir 
chown $sge_exec_user:$sge_exec_user $harvesting_dir 

if [ -f /opt/mnt.tgz ]
then
    tar -C /mnt/ -xvzf /opt/mnt.tgz
    # don't need to chown since files are already owned by www-data
fi


touch /tmp/python-eggs
chmod 777 /tmp/python-eggs