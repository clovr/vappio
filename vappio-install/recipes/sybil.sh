#!/bin/sh

# Pull the configure script down
#echo p | svn export --force https://svn.code.sf.net/p/ergatis/code/trunk/src/perl/configure_sybil.pl /mnt/configure_sybil.pl
wget -N -P /mnt/ https://dl.dropboxusercontent.com/u/15490934/configure_sybil.pl
#wget -N -P /mnt/ http://sybil.igs.umaryland.edu/configure_sybil.pl

# Pull the new prep_directories to avoid doing the bad chmod
#svn export http://vappio.svn.sf.net/svnroot/vappio/trunk/vappio-scripts/prep_directories.sh /opt/vappio-scripts/prep_directories.sh

#ssh -oNoneSwitch=yes -oNoneEnabled=yes -o PasswordAuthentication=no -o StrictHostKeyChecking=no -i /mnt/keys/devel1.pem root@localhost "perl /mnt/configure_sybil.pl --username=staphuser --password=staphuser123 --db_name=staph_aureus_v1 --db_url=http://sybil.igs.umaryland.edu/staph_aureus_v1.dump.gz --config_url=http://sybil.igs.umaryland.edu/staph_aureus_clovr_v1.conf --root_dir=/mnt/" &> /mnt/configure_sybil.log

perl /mnt/configure_sybil.pl --start_mongo --install_sybil --install_postgres --root_dir=/mnt/ &> /mnt/configure_sybil.log

# Grab the selfsim software which is needed to generate atypical nucleotide composition graphs                                                                                                                                                                                   
wget -O /tmp/selfsim.tgz https://dl.dropboxusercontent.com/u/15490934/selfsim.tgz                                                                                                                                                                                                
cd /tmp/
tar xfv /tmp/selfsim.tgz 
mv /tmp/selfsim /opt/opt-packages/selfsim-0.1 
ln -s /opt/opt-packages/selfsim-0.1/selfsim.bin /usr/local/bin/selfsim

rm /tmp/selfsim.tgz
