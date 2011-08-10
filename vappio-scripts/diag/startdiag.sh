#!/bin/bash

# Import vappio config
source /root/clovrEnv.sh
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh


mount /dev/sdb /mnt
chmod 777 /mnt

# Download scripts
export vappio_url_user_data=`cat /var/nimbus-metadata-server-url/*`/latest/user-data
mkdir -p $user_data_scripts
curl --retry 3 --silent --show-error --fail -o $user_data_scripts/metadata $vappio_url_user_data

# Use our default if none exists
FILE_SIZE=`wc -c $user_data_scripts/metadata | cut -f 1 -d ' '`
if [ "$FILE_SIZE" -eq "1" ]
then
    cp /opt/vappio-scripts/cli/master_user-data.default $user_data_scripts/metadata
    INSTANCE_DATA_URL=`cat /var/nimbus-metadata-server-url/*`
    AMI_ID=curl --retry 3 --silent --show-error --fail $INSTANCE_DATA_URL/latest/meta-data/ami-id
    sed -i -e 's/cluster\.ami=.*/cluster\.ami=$AMI_ID/' $user_data_scripts/metadata
fi

chmod +x $user_data_scripts/metadata

# Run user scripts
# TODO,split user data file into $user_data_scripts
# See /usr/lib/python2.6/dist-packages/cloudinit/UserDataHandler.py
if [ -d "$user_data_scripts" ]
then
    echo "Running user-scripts in $user_data_scripts"
    run-parts -v "$user_data_scripts"
fi
