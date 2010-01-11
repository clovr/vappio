#/bin/bash

#USAGE: ./saveami.sh [s3bucketname] [accesskey] [secretkey] [accountid]
usage="./saveami.sh [s3bucketname] [accesskey] [secretkey] [accountid]. See script comments for more information."

#
#INSTRUCTIONS
#You will need the 
#1)EC2 private key and cert
#2)Account information: accesskey,secretkey,accountid

#Steps

#1)From outside the cloud, copy amazon pk,cert keys to /mnt
#Don't worry, they will not be saved with the image
#Any changes in /mnt are ignored
#export EC2_PRIVATE_KEY=/mnt/pk-######.pem
#export EC2_CERT=/mnt/cert-####.pem

#2)Stop the master
#/opt/vappio-scripts/stop_master.sh

#3)Clean the master
#/etc/init.d/rc.local stop
#
#WARNING at this point you will not be able to login to the master if
#you lose your console. To "revive" the master for login at any point
#simply run /etc/init.d/rc.local start

#4)Run this script. Choose an image name as the first parameter
#/opt/vappio-scripts/amazonec2/saveami.sh clovr.9-04.x86-64.beta-v1r5b1-angiuolidevel-3.img $ACCESSKEY $SECRETKEY $ACCOUNTID

#Script follows
#######################
#Shutdown image and restart with new AMI
#Alternatively, you can revive this VM with /etc/init.d/rc.local start
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
source $vappio_scripts/amazonec2/ec2_config.sh
##
# Make sure node is out of SGE before backing up
case `cat /mnt/clovr/runtime/node_type` in
  OFFLINE) # do nothing
  ;;
  *)
    echo "node_type not OFFLINE. Run stop_master.sh and /etc/init.d/rc.local stop. Be sure to save ~/.ssh/authorized_keys so you can replace and login after creating the image"
    exit
  ;;
esac

bucketname=$1

if [ -z $bucketname ]
then
	echo $usage
	exit
fi 
accesskey=$2
if [ -z $accesskey ]
then
    echo $usage
    exit
fi
secretkey=$3
if [ -z $secretkey ]
then
    echo $usage
    exit
fi
accountid=$4
if [ -z $accountid ]
then
    echo $usage
    exit
fi

#Optionally unzip the kernel modules for amazon
#pushd /lib/
#gunzip -c $vappio_scripts/amazonec2/kernel-modules2616-xenu.tgz | tar -xvf -
#popd
#depmod -ae 2.6.16-xenU
rm -rf /mnt/$bucketname
mkdir /mnt/$bucketname
ec2-bundle-vol -c $EC2_CERT -k $EC2_PRIVATE_KEY -d /mnt/$bucketname -u $accountid -r x86_64 s
ec2-upload-bundle -b $bucketname -m /mnt/$bucketname/image.manifest.xml -a $accesskey -s $secretkey 
ec2-register $bucketname/image.manifest.xml 
