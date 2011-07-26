#!/bin/bash

# Import vappio config
source /root/clovrEnv.sh
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh


mount /dev/sdb /mnt

# Download scripts
export vappio_url_user_data=`cat /var/nimbus-metadata-server-url/*`/latest/user-data
mkdir -p $user_data_scripts
curl --retry 3 --silent --show-error --fail -o $user_data_scripts/metadata $vappio_url_user_data
chmod +x $user_data_scripts/metadata

# Run user scripts
# TODO,split user data file into $user_data_scripts
# See /usr/lib/python2.6/dist-packages/cloudinit/UserDataHandler.py
if [ -d "$user_data_scripts" ]
then
    echo "Running user-scripts in $user_data_scripts"
    run-parts -v "$user_data_scripts"
fi
