#!/bin/sh

wget http://prdownloads.sourceforge.net/scons/scons-2.3.0.tar.gz -O /tmp/scons-2.3.0.tar.gz
tar -C /tmp/ -xvf /tmp/scons-2.3.0.tar.gz
python2.7 /tmp/scons-2.3.0/setup.py install

rm -rf /tmp/scons-2.3.0/
