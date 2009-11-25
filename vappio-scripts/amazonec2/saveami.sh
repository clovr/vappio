#/bin/bash
#./saveami.sh [s3bucketname] [accesskey] [secretkey] [accountid] [wipe|nowipe]
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
source $vappio_scripts/amazonec2/ec2_config.sh
##
# Make sure node is out of SGE before backing up
case `cat /var/vappio_runtime/node_type` in
  OFFLINE) # do nothing
  ;;
  *)
    echo "node_type not OFFLINE"
    exit
  ;;
esac
bucketname=$1
if [ -z $bucketname ]
then
	echo "./saveami.sh [s3bucketname] [accesskey] [secretkey] [accountid] [wipe|nowipe]"
	exit
fi 
accesskey=$2
if [ -z $accesskey ]
then
    echo "./saveami.sh [s3bucketname] [accesskey] [secretkey] [accountid] [wipe|nowipe]"
    exit
fi
secretkey=$3
if [ -z $secretkey ]
then
    echo "./saveami.sh [s3bucketname] [accesskey] [secretkey] [accountid] [wipe|nowipe]"
    exit
fi
accountid=$4
if [ -z $accountid ]
then
    echo "./saveami.sh [s3bucketname] [accesskey] [secretkey] [accountid] [wipe|nowipe]"
    exit
fi

case $5 in
  "wipe")
    rm -rf /tmp/*
    #rm -rf /mnt/*
    rm -f /var/log/*.log
    rm ~/.bash_history
    rm /home/guest/*
  ;;
  "nowipe")
    echo "Keeping data in /tmp and /mnt"
  ;;
  *)
    echo "Specify wipe or nowipe"
    exit
  ;;
esac

$vappio_scripts/stop_master.sh
#Unzip the kernel modules for amazon
pushd /lib/
gunzip -c $vappio_scripts/amazonec2/kernel-modules2616-xenu.tgz | tar -xvf -
popd
depmod -ae 2.6.16-xenU
mkdir /mnt/$bucketname
$EC2_AMITOOL_HOME/bin/ec2-bundle-vol -c $EC2_CERT -k $EC2_PRIVATE_KEY -d /mnt/$bucketname -u $accountid -r i386 s
$EC2_AMITOOL_HOME/bin/ec2-upload-bundle -b $bucketname -m /mnt/$bucketname/image.manifest.xml -a $accesskey -s $secretkey 
$EC2_HOME/bin/ec2-register $bucketname/image.manifest.xml 
