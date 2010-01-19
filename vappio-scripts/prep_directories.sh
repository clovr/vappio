#import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

# prep_directories.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

#create local directories for workflows
for i in $harvesting_dir $staging_dir $wfworking_dir $scratch_dir $scratch_dir/ergatis;
do
  mkdir -p $i
  chmod 777 $i
done;

chown $sge_exec_user:$sge_exec_user $staging_dir 
chown $sge_exec_user:$sge_exec_user $wfworking_dir 
chown $sge_exec_user:$sge_exec_user $harvesting_dir 

# untar clovr ergatis project
mkdir -p /mnt/projects
tar -C /mnt/projects -xvzf /opt/project_clovr.tgz

# don't need to chown since files are already owned by www-data
