#!/bin/bash

# Install python2.7
apt-get -y --force-yes install python-software-properties
add-apt-repository ppa:fkrull/deadsnakes
apt-get -y --force-yes update
apt-get -y --force-yes install python2.7
apt-get -y --force-yes install python2.7-dev

# Install python modules
cd /tmp
git clone https://github.com/ged-lab/screed.git
git clone https://github.com/ged-lab/khmer.git

cd /tmp/khmer
git checkout tags/v0.8
make
cd python
python2.7 setup.py install

cd /tmp/screed
python2.7 setup.py install

rm -rf /tmp/khmer /tmp/screed
