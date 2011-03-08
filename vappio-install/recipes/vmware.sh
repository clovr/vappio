#!/bin/bash

#wget -c -P /tmp http://cb2.igs.umaryland.edu/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
#tar -C / -xvzf /tmp/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz

wget -c -P /tmp http://cb2.igs.umaryland.edu/VMwareTools-8.4.2-261058.tar.gz
tar -C /tmp -xvzf /tmp/VMwareTools-8.4.2-261058.tar.gz
/tmp/vmware-tools-distrib/vmware-install.pl --default
export ARCH=x86_64
mv /bin/uname /bin/uname.orig
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/util/fakeuname.sh /tmp/fakeuname.sh
cp /tmp/fakeuname.sh /bin/uname
#For installing the kernel modules
apt-get -y install build-essential
apt-get -y install linux-headers-`uname -r`
apt-get -y install linux-image-`uname -r`
vmware-config-tools.pl -d --overwrite --skip-stop-start

#Stop services by default
/etc/init.d/vmware-tools stop
update-rc.d -f vmware-tools remove
mv /bin/uname.orig /bin/uname

#Remove 70-persistent-net.rules on shutdown to prevent networking problems on subsequent boot
echo "rm -f /etc/udev/rules.d/70-persistent-net.rules" > /etc/init.d/rmudevnet
chmod +x /etc/init.d/rmudevnet
update-rc.d -f rmudevnet start 01 0

#
#Update to eliminate warnings
#/etc/udev/rules.d/99-vmware-scsi-udev.rules 
rm -f /etc/udev/rules.d/99-vmware-scsi-udev.rules*
