#!/bin/bash

sudo apt-get -y install zlib1g-dev libssl-dev libgcrypt11-dev libwrap0-dev libpam0g-dev
mkdir /tmp/hpn-sshsource
pushd /tmp/hpn-sshsource
wget http://cb2.igs.umaryland.edu/openssh-5.1p1hpn13v5.tar.gz
tar xvzf openssh-5.1p1hpn13v5.tar.gz
cd openssh-5.1p1hpn13v5
./configure --prefix=/usr --with-pam
make
make install
cd ../
#Deprecates
#wget http://cb2.igs.umaryland.edu/ssh_config.tgz
#tar -C / -xvzf ssh_config.tgz
#retrive sshd_config
rm -rf /etc/ssh
ln -s /usr/etc/ssh /etc/ssh 
popd
rm -rf /tmp/hpn-sshsource

