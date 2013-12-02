#!/bin/bash

wget -c -P /tmp/ http://sourceforge.net/projects/picard/files/picard-tools-1.103.zip
unzip /tmp/picard-tools-1.103.zip -d /tmp/

cp -R /tmp/picard-tools-1.103/ /opt/opt-packages/picard_tools-1.103/
rm -rf /tmp/picard-tools-1.03/ /tmp/picard-tools-1.103.zip 

