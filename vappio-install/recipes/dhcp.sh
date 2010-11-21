#!/bin/bash

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/dhcp3 $tmpdir/etc/dhcp3
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
rm -rf $tmpdir
