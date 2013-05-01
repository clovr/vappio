#!/bin/bash

# Install python2.7
apt-get -y --force-yes install python-software-properties
add-apt-repository ppa:fkrull/deadsnakes
apt-get -y --force-yes update
apt-get -y --force-yes install python2.7
apt-get -y --force-yes install python2.7-dev

# Install python modules
git clone https://github.com/ged-lab/screed.git /tmp/
git clone https://github.com/ged-lab/khmer.git /tmp/

cd /tmp/khmer
make
cd python
python2.7 setup.py install

cd /tmp/screed
python2.7 setup.py install

rm -rf /tmp/khmer /tmp/screed
