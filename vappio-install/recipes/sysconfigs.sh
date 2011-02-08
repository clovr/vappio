#!/bin/bash

#Set up some basic system settings to taste
#Including ulimit, kernel params

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc $tmpdir/root
echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/cloud $tmpdir/etc/cloud

echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.conf $tmpdir/etc/sysctl.conf
echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.d $tmpdir/etc/sysctl.d
echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/profile $tmpdir/etc/profile
echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/profile.d $tmpdir/etc/profile.d

echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/pam.d $tmpdir/etc/pam.d
echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/security $tmpdir/etc/security
echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/perl $tmpdir/etc/perl

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
echo 0 > /proc/sys/kernel/softlockup_thresh

#FUTEX_WAIT call possible fix
#rm /dev/random 
#mknod -m 644 /dev/random c 1 9 

chmod +t /tmp/
chmod 777 /tmp

echo "ahci" >> /etc/initramfs-tools/modules





