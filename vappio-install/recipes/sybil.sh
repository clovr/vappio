#!/bin/sh

# Pull the configure script down
wget -N -P /mnt/ http://sybil.igs.umaryland.edu/configure_sybil.pl

# Pull the new prep_directories to avoid doing the bad chmod
#svn export http://vappio.svn.sf.net/svnroot/vappio/trunk/vappio-scripts/prep_directories.sh /opt/vappio-scripts/prep_directories.sh

#ssh -oNoneSwitch=yes -oNoneEnabled=yes -o PasswordAuthentication=no -o StrictHostKeyChecking=no -i /mnt/keys/devel1.pem root@localhost "perl /mnt/configure_sybil.pl --username=staphuser --password=staphuser123 --db_name=staph_aureus_v1 --db_url=http://sybil.igs.umaryland.edu/staph_aureus_v1.dump.gz --config_url=http://sybil.igs.umaryland.edu/staph_aureus_clovr_v1.conf --root_dir=/mnt/" &> /mnt/configure_sybil.log

perl /mnt/configure_sybil.pl --install_mongo --install_sybil --install_postgres --root_dir=/mnt/ &> /mnt/configure_sybil.log
