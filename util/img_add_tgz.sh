#!/bin/bash

#USAGE:./img_add_tgz.sh image.img bundle.tgz
#
#./img_add_tgz.sh clovr_skeleton.img vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
#
#To add vmwaretools and vbox guest
#
#img_clean.sh clovr_skeleton.img /opt/vappio-util/cleanupimg
#cp clovr_skeleton.img clovr_skeleton.vmware.img
#
#img_add_tgz.sh clovr_skeleton.tools.img vmware-tools.8.4.2.tgz
#img_add_tgz.sh clovr_skeleton.tools.img vboxtools.tgz
#img_to_vmdk.sh clovr_skeleton.tools.img grub.tgz clovr_skeleton.vmdk
#bundle_vmx.sh clovr_skeleton.vmdk clovr.vmx clovr.9-04.x86-64.v1.vmx v1
#bundle_ovf.sh clovr_skeleton.vmdk clovr.ovf
#tar cvzf clovr_bundle.tgz clovr_skeleton.vmdk 

#Make sure image is not already mounted
ismounted=`losetup -j $1`
if [ "$ismounted" != "" ]
then
    echo "$1 already mounted as a device $ismounted. Run losetup -d to remove"
    exit 1 
fi

devname=`losetup --show -f $1`
mkdir /mnt/$$
mount $devname /mnt/$$
tar -C /mnt/$$ -xvzf $2
sync
umount /mnt/$$
losetup -d $devname
rmdir /mnt/$$
