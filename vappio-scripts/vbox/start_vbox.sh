#!/bin/sh

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/vbox/vbox_config.sh

/etc/init.d/vboxadd restart
/etc/init.d/vboxadd-service restart

# Mount VMware shared areas

if [ -f $vappio_runtime/no_dns ]
then
    nodns=1
fi

# Generic Shared area
mount -o ttl=3 -t vboxsf $shared_dir $shared_mp -o uid=33 -o gid=33
mount -o ttl=3 -t vboxsf $userdata_dir $userdata_mp -o uid=33 -o gid=33 -o fmask=000 -o dmask=000

# Postgres specific shared area
mount -o ttl=3 -t vboxsf $postgres_data_dir $postgres_data_dir_mp -o uid=$postgres_uid
mount -o ttl=3 -t vboxsf keys /mnt/keys -o uid=33 -o gid=33 -o fmask=077 -o dmask=077

# Required permissions for postgres
chmod 700 $postgres_data_dir_mp

# Should this copy files into the postgres directory if they don't exist?
if [ -e $postgres_data_dir_mp/postmaster.opts ]; then
    # Start the postgres server
    /etc/init.d/postgresql-8.3 start
else
    tar xzf $postgres_data_dir_tarball --no-same-owner -C $postgres_data_dir_mp
    echo 'Copied in an empty postgres data directory'
    /etc/init.d/postgresql-8.3 start
fi

# modify vappio_config.sh with the vmware-specific variables recorded in vmware_config.sh

echo "VBox" > $vappio_runtime/cloud_type

if [ "$nodns" == 1 ]
then
    touch $vappio_runtime/no_dns
fi

if [ -d /mnt/projects/clovr ]
then
    echo "Found CloVR project area"
else
    echo "Creating new project areas"
    $vappio_scripts/prep_directories.sh 1> /dev/null 2> /dev/null
fi

