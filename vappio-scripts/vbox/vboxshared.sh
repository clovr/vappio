#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/vbox/vbox_config.sh

#Add shared folder 
pushd /mnt
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/mnt/shared/ /mnt/
chmod 777 shared
popd
