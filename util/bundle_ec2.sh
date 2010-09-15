#!/bin/bash -e

USAGE="vp-bundle-ec2 [image.img|imagedir]"
#image.img - bundle and upload to EC2
#imagedir  - bundle and upload imagedir.img to EC2 and write AMI to imagedir/clovr.conf

if [ -d "$1" ]
then
    imagedir=$1
    image="$1.img"
else
    image=$1
fi

if [ ! -f "$image" ]
then
    echo "Can't find image $image"
    echo "$USAGE"
    exit 1
fi
if [ ! -f "/mnt/keys/ec2user" ] || [ ! -f "/mnt/keys/ec2account" ] || [ ! -f "/mnt/keys/ec2secretkey" ]
then
    echo "Save ec2 keys and account information in /mnt/keys"
    echo "Files: ec2user,ec2account,ec2secretkey,pk-*.pem,cert-*.pem"
    exit 2
fi

imgname=`basename $1`

source /root/clovrEnv.sh

export EC2_HOME=/opt/ec2-ami-tools-1.3-56066
export EC2_AMITOOL_HOME=/opt/ec2-ami-tools-1.3-56066

user=`cat /mnt/keys/ec2user`
account=`cat /mnt/keys/ec2account`
secretkey=`cat /mnt/keys/ec2secretkey`

mkdir -p /mnt/ec2bundles

if [ -f "/mnt/ec2bundles/$imgname.manifest.xml" ]
then
    echo "Found manifest, /mnt/ec2bundles/$imgname.manifest.xml, skipping ec2-bundle-image"
else
    echo "Bundling image $imgname"
    $EC2_AMITOOL_HOME/bin/ec2-bundle-image -c /mnt/keys/cert-*.pem -k /mnt/keys/pk-*.pem -u $user --kernel aki-0b4aa462  -i $image -d /mnt/ec2bundles -p $imgname -r x86_64
fi

#If not Access Denied, bucket does not exist
s3manifest=`curl --silent http://s3.amazonaws.com/$imgname | grep Access` || true
if [ "$s3manifest" = "" ]
then
    #Upload bundle
    echo "Uploading $imgname to S3"
    $EC2_AMITOOL_HOME/bin/ec2-upload-bundle -b $imgname -m /mnt/ec2bundles/$imgname.manifest.xml -a $account -s $secretkey
fi

export EC2_HOME=/opt/opt-packages/ec2-api-tools-1.3-53907/
export EC2_APITOOL_HOME=/opt/opt-packages/ec2-api-tools-1.3-53907/
export JAVA_HOME=/usr
echo "Registering on EC2 $imgname/$imgname.manifest.xml"
ami=`$EC2_APITOOL_HOME/bin/ec2-register $imgname/$imgname.manifest.xml -K /mnt/keys/pk-*.pem -C /mnt/keys/cert-*.pem -n $imgname | perl -ne '/^IMAGE\s+(ami-\S+)/;print $1,"\n"'`
echo "AMI: $ami"
$EC2_APITOOL_HOME/bin/ec2-modify-image-attribute -C /mnt/keys/cert-*.pem -K /mnt/keys/pk-*.pem $ami --launch-permission -a all
if [ -d "$imagedir" ]
then
    echo "Writing $ami to $imagedir/clovr.conf"
    perl -pi -e "s/^ami=.*/ami=$ami/" $imagedir/shared/vappio-conf/clovr.conf
else
    echo "Update clovr.conf on the image to reference this AMI: $ami"
fi
#update the tar
echo "Updating the tar"
if [ `basename $imagedir` = "/mnt/" ]
then
    dname=`dirname $imagedir`
    imagedir=`basename $imagedir`
    tar -C $dname cvzf $imagedir.tgz $imagedir
else
    tar cvzf $imagedir.tgz $imagedir    
fi
