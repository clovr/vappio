#!/bin/bash

#To recreate
#echo "CloVR" > etc/vappio/appliance_name
#echo "base" > etc/vappio/bundle_name
#date +%m%d%Y > etc/vappio/release_name

echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.bashrc /root/.bashrc
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/README /root/README

#Remove startup messages
rm -f /etc/update-motd.d/51_update-motd
rm -f /etc/update-motd.d/92-uec-upgrade-available

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc 
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/update-motd.d $tmpdir/etc/update-motd.d
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/issue $tmpdir/etc/issue
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
rm -rf $tmpdir
chmod 755 /etc

