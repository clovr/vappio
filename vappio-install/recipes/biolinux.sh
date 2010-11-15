#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

sudo add-apt-repository "deb http://nebc.nerc.ac.uk/bio-linux/ unstable bio-linux"
apt-get update
apt-get --force-yes -y install bio-linux-keyring
apt-get update

#TODO, consider merging with Ubuntu repository, see recipe ubuntuifxpkgs
apt-get -y --force-yes install bio-linux-base-directories bio-linux-bldp-files bio-linux-glimmer3 bio-linux-hmmer bio-linux-trnascan 

