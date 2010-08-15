#!/bin/bash

#Raw disk image to VMWare conversion
#Allows for conversion of Xen images to VMware
#S. Angiuoli 12/09

#This must all be performed as root or sudo-ed

# img_to_vmdk.sh <path_to_xen_image> <path_to_grub_tarball> <path_to_output_vmdk>

if [ $# -ne 3 ] 
    then
    echo "Usage: img_to_vmdk.sh <path_to_xen_image> <path_to_grub_tarball> <path_to_output_vmdk>"
    exit 2
fi

#create a new blank raw disk image of desired size, eg 10G
rm -f ./clovrVMware.raw
losetup -d /dev/loop1
losetup -d /dev/loop0

qemu-img create -f raw ./clovrVMware.raw 10G

#mount clovrVMware.raw as loopback device loop0
losetup /dev/loop0 ./clovrVMware.raw

#create a new partition with fdisk
#scripted to create 1 large, bootable partition
fdisk /dev/loop0 << .
n
p
1


a
1
w
.

#now we have a virtual hard drive aka /dev/loop0==/dev/hda
#We need partition 1 like /dev/hda1==/dev/loop1

fdisk -ul /dev/loop0

#Take sector start and covert to bytes 63*512=32256
#Now mount this partition as /dev/loop1

losetup -o 32256 /dev/loop1 /dev/loop0

#Now copy the image, already formatted ext3 partition into /dev/loop1
#ie. dump release image clovr-vXbXrX.raw in loopback loop1

dd if=$1 of=/dev/loop1

#could stop at this point and format blank partition as ext3
#mkfs.ext3 /dev/loop1
#Then run grub install and can save the /dev/loop1 file (eg. vmdktemplate.raw)
#This file can serve as a starting point for future conversions
#dd if=/tmp/clovr-vXbXrX.raw of=vmdktemplate.raw seek=32256
#This eliminates the need for root access to create mount point /dev/loop1
#Once this is done skip to the qemu-img convert process

#Ensure /boot includes a working kernel and grub files
#I have a copy in /usr/local/projects/CloVR/images/grub-boot.tgz
#This is the original boot directory from the Ubuntu 9.04 image from stacklet.com
#which serves as the base for CloVR.
rm -f /mnt/foo1
mkdir -p /mnt/foo1
mount /dev/loop1 /mnt/foo1
pushd /mnt/foo1
tar xvzf $2 boot/grub
#Write out zeros to better compress file system
dd if=/dev/zero of=tmp/ZEROS
sync
rm -f tmp/ZEROS
sync
popd
umount /mnt/foo1
v
#Now finally install boot loader on MBR of clovrVMware.raw==loop0
#sync

grub --device-map=/dev/null << .
device (hd0) /mnt/clovrVMware.raw 
root (hd0,0)
setup (hd0)
quit
.
#unmount
losetup -d /dev/loop1
sleep 2
losetup -d /dev/loop0

#We now have a bootable image in raw disk format, clovrVMWare.raw

#Proceed with the VMware conversion
#Create vmdk
qemu-img convert -f raw ./clovrVMware.raw -o compat6 -O vmdk $3

#Simply update an existing .vmx file to reference this vmdk
#And you are done 

tar -S -cvzf $3.tgz $3