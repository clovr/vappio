#!/bin/bash

#USAGE: img_clean.sh image.img cleanupscript.sh

devname=`losetup --show -f image.img`
rm -rf /mnt/$$
mkdir /mnt/$$
mount $devname /mnt/$$
chroot /mnt/$$ bash $2
umount /mnt/$$
losetup -d $devname
exit
