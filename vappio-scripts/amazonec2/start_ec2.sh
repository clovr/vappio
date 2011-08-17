#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"


sdir=/var/lib/cloud/data/scripts

if [ ! -d "$sdir" ]
then
    mkdir -p $sdir
fi

chmod 777 /mnt
chmod 777 /tmp

#Copy user-scripts off mount before new mount
cp /mnt/user_data/user_scripts/* $sdir

cloud-init start
cloud-init-cfg config-misc
cloud-init-cfg config-ssh
cloud-init-cfg config-mounts

chmod 777 /mnt
chmod 777 /tmp

#Run user-data scripts
#This can specify the node type and master node by writing the file
#$vappio_userdata/node_type
if [ -d "$sdir" ] 
then
    cloud-init-run-module once-per-instance user-scripts execute run-parts --regex '.*' "$sdir"
fi

#Background this for now
$vappio_scripts/create_swap_file.sh &

# Enter cloud only mode if not invoked by a clovr client VM
if [ ! -e "$vappio_runtime/clientmode" ]
then
    touch $vappio_runtime/cloudonlymode
    touch $vappio_runtime/noautoshutdown
    cp /opt/vappio-scripts/cli/master_user-data.default $vappio_runtime/cloudonly_metadata
    AMI_ID=`curl --retry 3 --silent --show-error --fail http://169.254.169.254/latest/meta-data/ami-id`
    sed -i -e "s/cluster\.ami=.*/cluster\.ami=$AMI_ID/" $vappio_runtime/cloudonly_metadata
    chmod +x $vappio_runtime/cloudonly_metadata
    $vappio_runtime/cloudonly_metadata
fi


