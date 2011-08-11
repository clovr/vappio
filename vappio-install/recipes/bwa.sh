#!/bin/bash

wget -c -P /tmp/ http://sourceforge.net/projects/bio-bwa/files/bwa-0.5.9.tar.bz2

tar -C /tmp -xjvf /tmp/bwa-0.5.9.tar.bz2

cd /tmp/bwa-0.5.9
make
cp /tmp/bwa-0.5.9/bwa /usr/local/bin/

