#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

sudo add-apt-repository "deb http://nebc.nerc.ac.uk/bio-linux/ unstable bio-linux"

# This is a hack to keep things working. It looks like the biolinux people are abandoning
# these older versions.
wget -P /tmp http://cb2.igs.umaryland.edu/trnascan-se_1.23-2_amd64.deb
dpkg --install /tmp/trnascan-se_1.23-2_amd64.deb

#sudo add-apt-repository "deb http://packages.sgn.cornell.edu/apt/ sgn main"
apt-get update
apt-get --force-yes -y install bio-linux-keyring
apt-get update

#TODO, consider merging with Ubuntu repository, see recipe ubuntuifxpkgs
apt-get -y --force-yes install bio-linux-shared bio-linux-bldp-files bio-linux-glimmer3 bio-linux-hmmer bio-linux-trnascan 

wget -O /usr/bin/tbl2asn http://cb2.igs.umaryland.edu/tbl2asn
