#!/bin/bash

## Installs and configures an instance of pureftpd on CloVR to facilitate
## large tranfers over FTP

# Setup a group + user to be associated with our virtual users
groupadd ftp
useradd -g ftp -d /dev/null -s /etc ftpuser

apt-get -y install pure-ftpd

# Create a temporary user to instantiate pure-ftp'd virtual user DB
echo "Setting up ftp users..."
PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
(echo ${PASSWORD}; echo ${PASSWORD}) | pure-pw useradd clovr -d /mnt/user_data/ -u ftpuser
pure-pw mkdb /etc/pure-ftpd/pureftpd.pdb

# Configure pure-ftpd to use virtual users
echo "Configuring pure-ftpd virtual users"
cd /etc/pure-ftpd/conf
echo 'no' > PAMAuthentication
echo 'no' > UnixAuthentication
echo '/etc/pure-ftpd/pureftpd.pdb' > PureDB
ln -s ../conf/PureDB /etc/pure-ftpd/auth/50pure
