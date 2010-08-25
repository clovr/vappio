#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/vmware/vmware_config.sh

#From
#http://communities.vmware.com/message/1063845#1063845
#echo "64" > /sys/block/sda/queue/max_sectors_kb # This depends on the block size of your RAID controller
#echo "8192" > /sys/block/sda/queue/nr_requests
#blockdev --setra 16384 /dev/sda
