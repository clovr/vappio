#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

chmod 777 /mnt
chmod 777 /tmp

cloud-init start
cloud-init-cfg config-misc
cloud-init-cfg config-ssh
cloud-init-cfg config-mounts

#Run user-data scripts
#This can specify the node type and master node by writing the file
#$vappio_userdata/node_type
sdir=/var/lib/cloud/data/scripts
[ -d "$sdir" ] || exit 0
cloud-init-run-module once-per-instance user-scripts execute run-parts --regex '.*' "$sdir"

#Background this for now
$vappio_scripts/create_swap_file.sh &



