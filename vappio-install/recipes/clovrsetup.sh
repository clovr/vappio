#!/bin/bash

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir

echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/mnt/shared/ $tmpdir/mnt/
#Must not install vappio-conf on ec2
rm -rf $tmpdir/mnt/vappio-conf

pushd $tmpdir/mnt
tar cvzf /opt/mnt.tgz .
popd

chmod a+rw /opt/mnt.tgz
