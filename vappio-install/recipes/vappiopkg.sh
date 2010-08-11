#!/bin/bash

pushd /tmp
rm -rf vappio-py
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py
export PYTHONPATH=$PYTHONPATH:/tmp/vappio-py
/tmp/vappio-py/vappio/cli/updateAllDirs.py --vappio-scripts --vappio-py --vappio-conf --vappio-py-www --config_policies
popd
rm -rf /tmp/vappio-py
#apache config from other

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init $tmpdir/etc/init
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/vappio $tmpdir/etc/vappio

svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sudoers $tmpdir/etc/sudoers
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
rm -rf $tmpdir
chmod 755 /etc
chmod 0440 /etc/sudoers


