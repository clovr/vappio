#!/bin/bash 

#USAGE:img_to_magellan image.img kernel_id ramdisk_id keys

#Assumes 

#~/.euca/eucarc installed per magellan instructions
#/mnt has lots of space 
#no loopback devices mounted
#kernels downloadable from http://cb2.igs.umaryland.edu

source ~/.euca/eucarc

kernel=eki-44811D5A
ramdisk=eri-1F621CD3

#Make sure image is not already mounted
ismounted=`losetup -j $1`
if [ "$ismounted" != "" ]
then
    echo "$1 already mounted as a device $ismounted. Run losetup -d to remove"
    exit 1 
fi
#Mount image and unzip kernel
losetup -a 
devname=`losetup --show -f $1`
mkdir /mnt/$$
mount $devname /mnt/$$
pushd /mnt/$$
#wget http://cb2.igs.umaryland.edu/magellan-$kernel.tgz
cp /root/magellan-$kernel.tgz .
cp /root/magellan_boot-$kernel.tgz .
tar xvzf magellan-$kernel.tgz
tar xvzf magellan_boot-$kernel.tgz
cp -f /root/libply-boot-client.so.2.0.0 lib/
rm -f magellan-$kernel.tgz
rm -f magellan_boot-$kernel.tgz
popd
#Zero out drive to recover space
dd if=/dev/zero of=/mnt/$$/tmp/ZEROS
sync
rm -f /mnt/$$/tmp/ZEROS
sync
umount /mnt/$$
losetup -d $devname
rmdir /mnt/$$

#Bundle with hard-coded kernel
euca-bundle-image -i $1 --kernel $kernel --ramdisk $ramdisk -d /mnt/

bname=`basename $1`

euca-upload-bundle -b $1 -m /mnt/$1.manifest.xml

euca-register $1/$1.manifest.xml

#To run
#myextip=`curl -s http://checkip.dyndns.org/ | xpath -e "//html/body" | perl -ne '/Address:\s+([^\<]+)/;print $1'`
#euca-authorize -P tcp -p 22 -s $myextip/32 default
#ec2-run-instances -t m1.large -k angiuoli-keys -n 1 -z Magellan2 -g default 