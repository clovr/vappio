#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt-get -y --force-yes install apache2

echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/init.d/apache2 /etc/init.d/apache2

/etc/init.d/apache2 stop

#TODO, break configs out of default into separate sites
tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir $tmpdir $tmpdir/etc
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/apache2 $tmpdir/etc/apache2
pushd $tmpdir
tar cvzf ../install$$.tgz .
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
chmod 755 /etc
rm -rf $tmpdir

# Add proxy modules
ln -f -s /etc/apache2/mods-available/proxy.load /etc/apache2/mods-enabled/
ln -f -s /etc/apache2/mods-available/proxy_http.load /etc/apache2/mods-enabled/
