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
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.d $tmpdir/etc/sysctl
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/cloud $tmpdir/etc/cloud
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/apt $tmpdir/etc/apt
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sysctl.conf $tmpdir/etc/sysctl.conf
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/profile $tmpdir/etc/profile
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/pam.d $tmpdir/etc/pam.d
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.profile $tmpdir/root/.profile
pushd $tmpdir
tar cvzf ../install$$.tgz .
tar xvzf -C / ../install$$.tgz
rm ../install$$.tgz
popd
rm -rf $tmpdir
#svn export root