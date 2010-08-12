#!/bin/bash -e

#Need grub legacy, it just works with xen
#tried grub2 but it is a mess
apt-get -y install grub
apt-get -y install qemu-kvm 

#Retrieve grub and boot sector 
wget -P /mnt http://cb2.igs.umaryland.edu/grub-boot.tgz


