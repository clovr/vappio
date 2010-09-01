#!/bin/bash 

USAGE="vp-buildall [image.img]
Defaults to /mnt/image.img. 
Make sure /mnt is an external mount with plenty of free space"

if [ "$1" = "" ]
then
    #if [ -f "/mnt/image.img.tgz" ]
    #then
	#This is broken, downstream segfault on chroot
	#loopback w/ chroot does not support sparse files
	#image="/mnt/image.img.tgz"
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
    #Trigger build through hudson or command line
    curl http://localhost:8888 > /dev/null
    if [ $? = 0 ]
    then
	curl http://localhost:8888/job/Build\%20$b\%20image/buildWithParameters?IMAGE_NAME=$image
    else
	/opt/vappio-util/build.sh $image $b
    fi
done
