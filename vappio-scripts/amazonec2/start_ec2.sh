#!/bin/sh

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

# environmental variables should be set here
source $vappio_scripts/amazonec2/ec2_config.sh

# modify vappio_config.sh with the ec2-specific variables recorded in ec2_config.sh
#mod_config harvesting_dir $ec2_harvesting_dir
#mod_config staging_dir $ec2_staging_dir 

# append public key to authorized_keys
# instructions from http://docs.amazonwebservices.com/AWSEC2/latest/DeveloperGuide/index.html?building-shared-amis.html

# Wait until networking is up on the EC2 instance.
perl -MIO::Socket::INET -e '
 until(new IO::Socket::INET("169.254.169.254:80")){print "Waiting for network...\n";sleep 1}
' 

curl --retry 3 --silent --show-error --fail http://169.254.169.254/latest/meta-data/public-keys/0/openssh-key > /tmp/my-key
if [ $? -eq 0 ] ; then
	vlog "curl of public-key and appending to authorized_keys"
        cat /tmp/my-key >> /root/.ssh/authorized_keys
        chmod 700 /root/.ssh/authorized_keys
        rm /tmp/my-key
fi

# mount data filesystem
mount -t ext3 /dev/sdb $ec2_localmount
$vappio_scripts/prep_directories.sh 

# check for supplied user-data and potentially run it
echo "EC2" > $vappio_runtime/cloud_type
$vappio_scripts/run_user_data.sh

$vappio_scripts/create_swap_file.sh
