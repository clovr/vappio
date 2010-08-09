#!/bin/bash

#To recreate
#echo "CloVR" > etc/appliance_name
#echo "base" > etc/bundle_name
#date +%m%d%Y > etc/release_name

rm /etc/update-motd.d/51_update-motd
rm /etc/update-motd.d/92-uec-upgrade-available

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc $tmpdir/root
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/update-motd.d $tmpdir/etc/update-motd.d
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
rm -rf $tmpdir
chmod 755 /etc

