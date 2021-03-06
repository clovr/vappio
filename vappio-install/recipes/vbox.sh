#!/bin/sh

wget -c -P /tmp http://bioifx.org/vboxtools-install_05082012.tgz

tar -C / -xvzf /tmp/vboxtools-install_05082012.tgz

#Need to fake out uname so we compile for any kernel we want to run in vbox
mv /bin/uname /bin/uname.orig
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/util/fakeuname.sh /tmp/fakeuname.sh
cp /tmp/fakeuname.sh /bin/uname
#For installing the kernel modules
apt-get -y install build-essential
apt-get -y install linux-headers-`uname -r`
apt-get -y install linux-image-`uname -r`
mv /bin/uname.orig /bin/uname 

#
#Originally pulled installer from mount /dev/cdrom1 /mnt
#MUST USE SUDO or something strange happens
export ARCH=x86_64
sudo bash /tmp/VBoxLinuxAdditions.run
depmod -a

update-rc.d -f vboxadd-x11 remove
update-rc.d -f vboxadd-service remove
update-rc.d -f vboxadd remove
update-rc.d -f vboxdrv remove

apt-get -y install virtualbox-ose-fuse



