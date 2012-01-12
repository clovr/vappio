#!/bin/bash

apt-get -y install xstow

#Needed for vappio API
apt-get -y install python-setuptools
apt-get -y install python-pip
pip install pymongo==2.0.1

pushd /tmp
rm -rf vappio-py
echo p | svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py
export PYTHONPATH=$PYTHONPATH:/tmp/vappio-py
/tmp/vappio-py/vappio/cli/updateAllDirs.py --vappio-scripts --vappio-py --vappio-py-www --vappio-twisted --vappio-apps --config_policies
popd
rm -rf /tmp/vappio-py
#apache config from other

tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init $tmpdir/etc/init
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/rsyslog.d $tmpdir/etc/rsyslog.d
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/logrotate.d $tmpdir/etc/logrotate.d
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/vappio $tmpdir/etc/vappio

echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/sudoers $tmpdir/etc/sudoers
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


#Add basic help
echo p | svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/update-motd.d/10-help-text /etc/update-motd.d/10-help-text

