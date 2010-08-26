#!/bin/sh

wget -c -P /tmp http://cb2.igs.umaryland.edu/vboxtools-install.tgz

#For installing the guest 
mv /bin/uname /bin/uname.orig
cp /opt/vappio-util/fakeuname.sh /bin/uname
apt-get -y install build-essential
apt-get -y install linux-headers-`uname -r`

#mount /dev/cdrom1 /mnt
#MUST USE SUDO or something strange happens
sudo bash /tmp/VBoxLinuxAdditions-amd64.run
mv /bin/uname.orig /bin/uname