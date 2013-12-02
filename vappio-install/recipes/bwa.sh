#!/bin/bash

wget -c -P /tmp/ http://sourceforge.net/projects/bio-bwa/files/bwa-0.7.5a.tar.bz2
tar -C /tmp -xjvf /tmp/bwa-0.7.5a.tar.bz2

cd /tmp/bwa-0.7.5a
make
cp -R /tmp/bwa-0.7.5a /opt/opt-packages/

