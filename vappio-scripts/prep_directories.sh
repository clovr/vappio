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

if [ -f /opt/mnt.tgz ] && [ ! -f /mnt/.clovrmntconfig ]
then 
    tar -C /mnt/ -xkvzf /opt/mnt.tgz
    chown -R www-data.www-data /mnt
    touch /mnt/.clovrmntconfig
fi

touch /tmp/python-eggs
chmod 777 /tmp/python-eggs