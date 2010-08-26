#!/bin/bash 

#Need grub legacy, it just works with xen
#tried grub2 but it is a mess
apt-get -y install grub
#update-grub
apt-get -y install qemu-kvm 

#virtualbox utilities, need VBoxManage
#apt-get -y install virtualbox-ose

wget -q http://download.virtualbox.org/virtualbox/debian/oracle_vbox.asc -O- | sudo apt-key add -

sudo add-apt-repository "deb http://download.virtualbox.org/virtualbox/debian lucid non-free"
apt-get update
apt-get -y install virtualbox-3.2

#Retrieve grub and boot sector 
wget -c -P /mnt http://cb2.igs.umaryland.edu/grub-boot.tgz
#Retrive vmware tools
wget -c -P /mnt http://cb2.igs.umaryland.edu/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
#Retrive vmware tools
#wget -c -P /mnt http://cb2.igs.umaryland.edu/vboxtools-3.2.6.tar.gz
wget -c -P /mnt http://cb2.igs.umaryland.edu/VBoxLinuxAdditions-amd64.run

