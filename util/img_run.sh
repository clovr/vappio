#!/bin/bash

#USAGE: img_run.sh image.img cleanupscript.sh

devname=`losetup --show -f image.img`
rm -rf /mnt/$$
mkdir /mnt/$$
mount $devname /mnt/$$
mount --bind /proc /mnt/$$/proc
mount --bind /sys /mnt/$$/sys
mount --bind /dev /mnt/$$/dev
chroot /mnt/$$ bash $2
umount /mnt/$$/proc
umount /mnt/$$/sys
umount /mnt/$$/dev
umount /mnt/$$
losetup -d $devname
exit
