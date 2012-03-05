#!/bin/sh


installvboxtools=$1

if [ "$installvboxtools" == "yes" ]
then
    wget -c -P /tmp http://cb2.igs.umaryland.edu/vboxtools-install.tgz
    
    tar -C / -xvzf /tmp/vboxtools-install.tgz
    
#Need to fake out uname so we compile for any kernel we want to run in vbox
    mv /bin/uname /bin/uname.orig
    echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/util/fakeuname.sh /tmp/fakeuname.sh
    cp /tmp/fakeuname.sh /bin/uname
#For installing the kernel modules
    apt-get -y install build-essential
    apt-get -y install linux-headers-`uname -r`
    apt-get -y install linux-image-`uname -r`
    
#
#Originally pulled installer from mount /dev/cdrom1 /mnt
#MUST USE SUDO or something strange happens
    sudo bash /tmp/VBoxLinuxAdditions-amd64.run
    depmod -a
    mv /bin/uname.orig /bin/uname
    update-rc.d -f vboxadd-x11 remove
    update-rc.d -f vboxadd-service remove
    update-rc.d -f vboxadd remove
    update-rc.d -f vboxdrv remove
    
    apt-get -y install virtualbox-ose-fuse
fi


