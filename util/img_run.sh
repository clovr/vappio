#!/bin/bash

#USAGE: img_run.sh image.img cmd
#Mounts image as loopback, copies CMD onto the image and runs

devname=`losetup --show -f $1`
rm -rf /mnt/$$
mkdir /mnt/$$

mount $devname /mnt/$$
mount --bind /proc /mnt/$$/proc
mount --bind /sys /mnt/$$/sys
mount --bind /dev /mnt/$$/dev

#copy command onto the image
bname=`basename $2`
cp $2 /mnt/$$/tmp/$bname
#Run the command
chroot /mnt/$$ bash /mnt/$$/tmp/$bname

umount /mnt/$$/proc
umount /mnt/$$/sys
umount /mnt/$$/dev
umount /mnt/$$
losetup -d $devname

exit
