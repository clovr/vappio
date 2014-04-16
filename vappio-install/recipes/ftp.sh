#!/bin/bash

## Installs and configures an instance of pureftpd on CloVR to facilitate
## large tranfers over FTP

# Setup a group + user to be associated with our virtual users
groupadd ftp
useradd -g ftp -d /dev/null -s /etc ftpuser

apt-get -y install pure-ftpd

# Create a temporary user to instantiate pure-ftp'd virtual user DB
echo "Generating random password..."
PASSWORD=`python -c "import uuid; id = uuid.uuid4(); print str(id).upper().replace('-', '')[0:10]"`
(echo ${PASSWORD}; echo ${PASSWORD}) | pure-pw useradd test -d /mnt/user_data/ -u ftpuser -m

echo "Writing pure-ftpd database..."
pure-pw mkdb /etc/pure-ftpd/pureftpd.pdb

# Configure pure-ftpd to use virtual users
echo "Configuring pure-ftpd virtual users"
cd /etc/pure-ftpd/conf
echo 'no' > PAMAuthentication
echo 'no' > UnixAuthentication
echo 'yes' > KeepAllFiles
echo '/etc/pure-ftpd/pureftpd.pdb' > PureDB
ln -s ../conf/PureDB /etc/pure-ftpd/auth/50pure

# Shut down ftp server; should run only when we have cloud-only mode
/etc/init.d/pure-ftpd stop
