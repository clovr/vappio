#!/bin/bash

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir

echo p | svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/mnt/shared/ $tmpdir/mnt/

pushd $tmpdir/mnt
tar cvzf /opt/mnt.tgz .
popd

chmod a+rw /opt/mnt.tgz
