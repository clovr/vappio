#!/bin/bash

#Set up some basic system settings to taste
iIncluding ulimit, kernel params

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc $tmpdir/root
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/cloud $tmpdir/etc/cloud

svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.conf $tmpdir/etc/sysctl.conf
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.d $tmpdir/etc/sysctl.d
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/profile $tmpdir/etc/profile
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/profile.d $tmpdir/etc/profile.d

svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/pam.d $tmpdir/etc/pam.d
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/security $tmpdir/etc/security
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/perl $tmpdir/etc/perl

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

chmod +t /tmp/
chmod 777 /tmp






