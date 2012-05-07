#!/bin/bash

#wget -c -P /tmp http://cb2.igs.umaryland.edu/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
#tar -C / -xvzf /tmp/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz

wget -c -P /tmp http://bioifx.org/VMwareTools-8.4.2-261058.tar.gz
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
mv /bin/uname.orig /bin/uname


#Stop services by default
/etc/init.d/vmware-tools stop
update-rc.d -f vmware-tools remove


