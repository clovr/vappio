#!/bin/bash

#Set up some basic system settings to taste
#Including ulimit, kernel params
#Enable root logins and passwordless console

#etc/profile
#etc/sysctl.conf
#/etc/pamd.conf/common-session
#/root/.profile
#/etc/apt/
#/etc/security/
#/etc/cloud/ #Change /etc/cloud/cloud.cfg:disable_root: 0
#/etc/pam.d/
#/etc/sysctl.d/

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc $tmpdir/root
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.d $tmpdir/etc/sysctl
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/cloud $tmpdir/etc/cloud
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/apt $tmpdir/etc/apt

svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.conf $tmpdir/etc/sysctl.conf
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.d $tmpdir/etc/sysctl.d
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/profile $tmpdir/etc/profile
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/hosts.orig $tmpdir/etc/hosts.orig
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/pam.d $tmpdir/etc/pam.d
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/security $tmpdir/etc/security
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/perl $tmpdir/etc/perl

#Contains SCREENME envvar for triggering screen on login
#TODO, this can cause problems for all shells spawned by SGE, make sure SCREENME is not set outside of login console
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.autologin $tmpdir/root/.autologin
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.clovr-login $tmpdir/root/.clovr-login
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.profile $tmpdir/root/.profile


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

#Allow root login
perl -pi -e 's/command=".*"\s+//' /root/.ssh/authorized_keys  
/etc/init.d/ssh restart

#Enable autologin for terminal
apt-get -y install mingetty
rm -f /etc/init/tty1.conf
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init/tty1.conf /etc/init/tty1.conf
#perl -pi -e 's/^exec.*/exec \/sbin\/mingetty \-\-autologin root tty1/' /etc/init/tty1.conf

#Setup hostname
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init.d/hostnamecheck /etc/init.d/hostnamecheck
/etc/init.d/hostnamecheck start

#Make non-EC apt the default
cp /etc/apt/sources.list.orig /etc/apt/sources.list

