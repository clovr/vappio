#!/bin/bash

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir

echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/mnt/shared/ $tmpdir/mnt/

pushd $tmpdir/mnt
tar cvzf /opt/mnt.tgz .
popd

chmod a+rw /opt/mnt.tgz
