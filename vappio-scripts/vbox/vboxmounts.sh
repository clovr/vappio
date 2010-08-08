#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/vbox/vbox_config.sh

# Generic Shared area
mount -o ttl=3 -t vboxsf $shared_dir $shared_mp -o uid=33 -o gid=33
mount -o ttl=3 -t vboxsf $userdata_dir $userdata_mp -o uid=33 -o gid=33 -o fmask=000 -o dmask=000
mount -o ttl=3 -t vboxsf keys $keysdir -o uid=33 -o gid=33 -o fmask=077 -o dmask=077

# Postgres specific shared area
mount -o ttl=3 -t vboxsf $postgres_data_dir $postgres_data_dir_mp -o uid=$postgres_uid
