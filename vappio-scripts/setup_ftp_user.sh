#!/bin/bash

## Configures CloVR FTP user for a remote master node

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/clovrEnv.sh
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

if [ -e "/etc/pure-ftpd/ftp_passwd" ]
then
    verror "FTP password file already exists. Perhaps FTP has already been configured?"
    echo "FTP password file already exists. Perhaps FTP has already been configured?"
    exit 1;
fi

PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 7 | head -n 1)
echo -e "${PASSWORD}\n${PASSWORD}" > /etc/pure-ftpd/ftp_passwd

pure-pw useradd clovr -u ftpuser -d /mnt/user_data -m < /etc/pure-ftpd/ftp_passwd

# We'll need to restart pureftpd to get the changes to stick
/etc/init.d/pure-ftpd restart
