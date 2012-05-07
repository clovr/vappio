#!/bin/bash

export ARCH=x86_64
mv /bin/uname /bin/uname.orig
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/util/fakeuname.sh /tmp/fakeuname.sh
cp /tmp/fakeuname.sh /bin/uname

#vmwaretools=VMwareTools-8.4.2-261058.tar.gz
vmwaretools=VMwareTools-8.4.8-491717.tar.gz
wget -c -P /tmp http://bioifx.org/$vmwaretools
tar -C /tmp -xvzf /tmp/$vmwaretools
/tmp/vmware-tools-distrib/vmware-install.pl --default

#For installing the kernel modules
apt-get -y install build-essential
apt-get -y install linux-headers-`uname -r`
apt-get -y install linux-image-`uname -r`
vmware-config-tools.pl -d --overwrite --skip-stop-start
mv /bin/uname.orig /bin/uname


#Stop services by default
/etc/init.d/vmware-tools stop
update-rc.d -f vmware-tools remove


