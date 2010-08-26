#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

sudo add-apt-repository "deb http://nebc.nerc.ac.uk/bio-linux/ unstable bio-linux"
apt-get update
#apt-get update
apt-get --force-yes -y install bio-linux-keyring
apt-get update
#TODO, consider removing bio-linux-blast bioperl bio-linux-mummer bio-linux-hmmer
#Replace tigr-glimmer bio-linux-glimmer3
apt-get -y --force-yes install dialign hmmer mummer primer3 emboss emboss-data emboss-lib ncbi-data ncbi-tools-bin bio-linux-base-directories bio-linux-blast bio-linux-bldp-files bio-linux-glimmer3 bio-linux-hmmer bio-linux-mummer bio-linux-trnascan bioperl biosquid blast2 blt 

