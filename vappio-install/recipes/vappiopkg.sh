#!/bin/bash

pushd /tmp
rm -rf vappio-py
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py
export PYTHONPATH=$PYTHONPATH:/tmp/vappio-py
updateAllDirs.py --vappio-scripts --vappio-py --vappio-conf --vappio-py-www --config_policies
popd
rm -rf /tmp/vappio-py
#apache config from other

#install /etc/init.d/vp_cfgapt /etc/init.d/vp_cfgaptec2 /etc/init.d/vp_cfghostname

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc $tmpdir/root
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/init/ $tmpdir/etc/init
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/vappio $tmpdir/etc/vappio
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sudoers $tmpdir/etc/sudoers
pushd $tmpdir
tar cvzf ../install$$.tgz .
tar xvzf -C / ../install$$.tgz
rm ../install$$.tgz
popd
rm -rf $tmpdir


