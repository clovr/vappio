#!/bin/bash

#Followed
#http://maketecheasier.com/change-login-and-boot-screen-in-ubuntu-lucid/2010/05/13

#Need to reset menu.1st vga=0x0314 800x600, vga=0x0311 640x480

apt-get install plymouth-theme-ubuntu-logo

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

#Update menu.1st
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/boot/grub/menu.1st.clovr /boot/grub/menu.1st
sudo update-initramfs -u -k `uname -r`





