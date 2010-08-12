#!/bin/bash

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
#TODO, this can cause problems for all shells spawned by SGE, make sure this is not set outside of login console
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.profile $tmpdir/root/.profile

pushd $tmpdir
tar cvzf ../install$$.tgz .
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
chmod 755 /etc
#rm -rf $tmpdir
#svn export --force  root

sysctl -p
ifconfig eth0 mtu 9000
ifconfig eth0 txqueuelen 50000

chmod +t /tmp/
chmod 777 /tmp
