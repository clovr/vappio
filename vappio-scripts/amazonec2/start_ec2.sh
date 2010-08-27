#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

cloud-init start
cloud-init-cfg config-misc
cloud-init-cfg config-ssh
cloud-init-cfg config-mounts

chmod 777 /mnt

#Run user-data scripts
#This can specify the node type and master node by writing the file
#$vappio_userdata/node_type
sdir=/var/lib/cloud/data/scripts
[ -d "$sdir" ] || exit 0
cloud-init-run-module once-per-instance user-scripts execute run-parts --regex '.*' "$sdir"

$vappio_scripts/create_swap_file.sh

# environmental variables should be set here
#source $vappio_scripts/amazonec2/ec2_config.sh

# append public key to authorized_keys
# instructions from http://docs.amazonwebservices.com/AWSEC2/latest/DeveloperGuide/index.html?building-shared-amis.html

# Wait until networking is up on the EC2 instance.
#perl -MIO::Socket::INET -e '
# until(new IO::Socket::INET("169.254.169.254:80")){print "Waiting for network...\n";sleep 1}
#' 

#curl --retry 3 --silent --show-error --fail http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key > /tmp/my-key
#if [ $? -eq 0 ] ; then
#	vlog "curl of public-key and appending to authorized_keys"
#        cat /tmp/my-key >> /root/.ssh/authorized_keys
#        chmod 700 /root/.ssh/authorized_keys
#        rm /tmp/my-key
#fi

# mount data filesystem
#mount -t ext3 /dev/sdb $ec2_localmount
#$vappio_scripts/prep_directories.sh 

# check for supplied user-data and potentially run it
#echo "EC2" > $vappio_runtime/cloud_type
#echo "OFFLINE-PENDING" > $vappio_runtime/node_type
#$vappio_scripts/run_user_data.sh



