#!/bin/sh

wget -c -P /tmp http://cb2.igs.umaryland.edu/vboxtools-install.tgz

tar -C / -xvzf /tmp/vboxtools-install.tgz

#Need to fake out uname so we compile for any kernel we want to run in vbox
mv /bin/uname /bin/uname.orig
cp /opt/vappio-util/fakeuname.sh /bin/uname
#For installing the kernel modules
apt-get -y install build-essential
apt-get -y install linux-headers-`uname -r`

#
#Originally pulled installer from mount /dev/cdrom1 /mnt
#MUST USE SUDO or something strange happens
sudo bash /tmp/VBoxLinuxAdditions-amd64.run
depmod -a
mv /bin/uname.orig /bin/uname