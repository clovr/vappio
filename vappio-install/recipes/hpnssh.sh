#!/bin/bash

sudo apt-get -y install zlib1g libssl-dev libgcrypt11-dev libwrap0-dev libpam0g-dev binutils
mkdir -p /tmp/hpn-sshsource
pushd /tmp/hpn-sshsource
wget http://cb2.igs.umaryland.edu/openssh-5.1p1hpn13v5.1.tar.gz
tar xvzf openssh-5.1p1hpn13v5.1.tar.gz
cd openssh-5.1p1hpn13v5
./configure --prefix=/usr --with-pam
make
make install
cd ../
#Deprecates
#wget http://cb2.igs.umaryland.edu/ssh_config.tgz
#tar -C / -xvzf ssh_config.tgz
#retrive sshd_config
tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir -p $tmpdir $tmpdir/usr/etc
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/usr/etc $tmpdir/usr/etc
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd
rm -rf /etc/ssh
ln -f -s /usr/etc /etc/ssh
perl -pi -e 's/command=".*"\s+//' /root/.ssh/authorized_keys  
/etc/init.d/ssh restart
popd
rm -rf /tmp/hpn-sshsource
rm -rf $tmpdir
