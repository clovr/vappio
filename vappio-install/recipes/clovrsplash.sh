#!/bin/bash

#install kernel mods
apt-get -y install build-essential
apt-get -y install linux-headers-`uname -r`
apt-get -y install linux-image-`uname -r`

#Not being used?
rename -f 's/plymouth(\S*)\.conf\.disabled/plymouth$1.conf/' /etc/init/plymouth*.conf.disabled

svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/boot /boot/

#Get base theme
apt-get -y install plymouth-theme-ubuntu-logo

#Made custom theme following
#http://maketecheasier.com/change-login-and-boot-screen-in-ubuntu-lucid/2010/05/13
#update-alternatives --install /lib/plymouth/themes/default.plymouth default.plymouth /lib/plymouth/themes/mytheme/mytheme.plymouth 100

#Get theme
wget -P /lib/plymouth/themes/ http://cb2.igs.umaryland.edu/plymouth-clovr.tgz
pushd /lib/plymouth/themes/
tar xvzf plymouth-clovr.tgz
popd

#Change theme to clovr
update-alternatives --install /lib/plymouth/themes/default.plymouth default.plymouth /lib/plymouth/themes/clovr/clovr.plymouth 100
#sudo update-alternatives --config default.plymouth
sudo update-alternatives --set default.plymouth /lib/plymouth/themes/clovr/clovr.plymouth

#Enable framebuffer
echo "FRAMEBUFFER=y" > /etc/initramfs-tools/conf.d/splash

#Keep this disabled for now
#mv -f /etc/modprobe.d/blacklist-framebuffer.conf /etc/modprobe.d/blacklist-framebuffer.conf.disabled

#Update menu.1st
#Need to reset menu.1st vga=0x0314 800x600, vga=0x0311 640x480
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/boot/grub/menu.lst.clovr /boot/grub/menu.lst
sudo update-initramfs -u -k `uname -r`





