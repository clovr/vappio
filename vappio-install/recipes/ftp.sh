#!/bin/bash

## Installs and configures an instance of pureftpd on CloVR to facilitate
## large tranfers over FTP

# Setup a group + user to be associated with our virtual users
groupadd ftp
useradd -g ftp -d /dev/null -s /etc ftpuser

apt-get -y install pure-ftpd

# Configure pure-ftpd to use virtual users
cd /etc/pure-ftpd/conf
echo 'no' > PAMAuthentication
echo 'no' > UnixAuthentication
echo '/etc/pure-ftpd/pureftpd.pdb' > PureDB
ln -s ../conf/PureDB /etc/pure-ftpd/auth/50pure
