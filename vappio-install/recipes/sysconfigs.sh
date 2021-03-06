#!/bin/bash

#Set up some basic system settings to taste
#Including ulimit, kernel params

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc $tmpdir/root
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/cloud $tmpdir/etc/cloud

echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/sysctl.conf $tmpdir/etc/sysctl.conf
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/sysctl.d $tmpdir/etc/sysctl.d
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/profile $tmpdir/etc/profile
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/profile.d $tmpdir/etc/profile.d

echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/pam.d $tmpdir/etc/pam.d
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/security $tmpdir/etc/security
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/perl $tmpdir/etc/perl

pushd $tmpdir
tar cvzf ../install$$.tgz .
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
chmod 755 /etc
rm -rf $tmpdir

sysctl -p

#This causes errors on vmware
#ifconfig eth0 mtu 9000
#ifconfig eth0 txqueuelen 50000

#Heavy disk IO can trigger hung task warnings in the VM
echo 0 > /proc/sys/kernel/hung_task_timeout_secs
#Removed from recent kernels
#echo 0 > /proc/sys/kernel/softlockup_thresh

#FUTEX_WAIT call possible fix
#rm /dev/random 
#mknod -m 644 /dev/random c 1 9 

chmod +t /tmp/
chmod 777 /tmp

echo "ahci" >> /etc/initramfs-tools/modules

#Remove 70-persistent-net.rules on shutdown to prevent networking problems on subsequent boot
echo "rm -f /etc/udev/rules.d/70-persistent-net.rules" > /etc/init.d/rmudevnet
chmod +x /etc/init.d/rmudevnet
update-rc.d -f rmudevnet start 01 0 .


#
#Update to eliminate warnings
#/etc/udev/rules.d/99-vmware-scsi-udev.rules 
rm -f /etc/udev/rules.d/99-vmware-scsi-udev.rules*




