#!/bin/bash

wget -c -P /tmp/ https://bedtools.googlecode.com/files/BEDTools.v2.17.0.tar.gz
tar -C /tmp -xvf /tmp/BEDTools.v2.17.0.tar.gz

cd /tmp/bedtools-2.17.0
make

cp -R /tmp/bedtools-2.17.0 /opt/opt-packages/
rm -rf /tmp/bedtools-2.17.0 /tmp/BEDTools.v2.17.0.tar.gz

