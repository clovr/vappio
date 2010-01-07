#!/bin/sh

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/vmware/vmware_config.sh

# Mount VMware shared areas

# Generic Shared area
mount -o ttl=3 -t vmhgfs .host:$shared_dir $shared_mp

# Postgres specific shared area
mount -o ttl=3 -t vmhgfs .host:$postgres_data_dir $postgres_data_dir_mp -o uid=$postgres_uid

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


# know /var/nimbus-metadata-server-url has to exist
#curl -f -s $vappio_url_user_data
#curl http://128.135.125.124:8081/2008-08-08/user-data
#$vappio_scripts/run_user_data.sh
