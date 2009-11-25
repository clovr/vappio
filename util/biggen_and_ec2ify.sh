#!/bin/bash
# Download an image from Nimbus, increase the size, and bundle and upload for EC2
source ~/.ec2-keys/ec2rc.sh
IMAGE=$1

/export/prog/nimbus-cloud-client-013/bin/cloud-client.sh --download --name $IMAGE.gz --localfile $IMAGE.gz
gunzip $IMAGE.gz
chmod 777 $IMAGE
#for i in 1 2 3 4 5; do
#dd if=/dev/zero bs=1024k count=1024 >> $IMAGE
#done
#/sbin/e2fsck -f $IMAGE
#/sbin/resize2fs $IMAGE
#/sbin/e2fsck -f $IMAGE

# or -r i386 if its 32bit
ec2-bundle-image -c $EC2_CERT -k $EC2_PRIVATE_KEY -u $EC2_ACCOUNT_ID --ec2cert /export/prog/ec2-tools/etc/ec2/amitools/cert-ec2.pem -i $IMAGE -d /local/scratch/agussman/ec2/ -p $IMAGE -r x86_64
# underscores in bucket name are not S3 v2 safe
ec2-upload-bundle -b $IMAGE -m /local/scratch/agussman/ec2/$IMAGE.manifest.xml -a $EC2_ACCESS_KEY_ID -s $EC2_SECRET_ACCESS_KEY
ec2-register $IMAGE/$IMAGE.manifest.xml


