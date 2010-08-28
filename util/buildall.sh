#!/bin/bash -e

#USAGE:buildall.sh [image.img]
#Defaults to /mnt/image.img. Make sure /mnt has enough free space

if [ "$1" = "" ]
then
    image="/mnt/image.img"
else
    image=$1
fi

if [ ! -f "$image" ]
then
    echo "Image file $image not found"
fi

mountpoint /mnt
if [ $? != 0 ]
then
    echo "/mnt must be an external mount with sufficient free space. mount this volume first"
    exit 1
fi

/opt/vappio-install/vp-bootstrap-install
bundles=`ls /opt/vappio-install/bundles | grep -`
echo "Bundles $bundles"
for b in $bundles
do
    echo "Building $b"
    /opt/vappio-util/build.sh $image $b
done
