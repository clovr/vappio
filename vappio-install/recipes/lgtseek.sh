#!/bin/bash

wget -P /tmp/ https://github.com/rileydavidr/lgtseek/archive/master.zip
unzip -o /tmp/master.zip -d /tmp/
cp -r /tmp/lgtseek-master /opt/opt-packages
ln -sf /opt/opt-packages/lgtseek-master /opt/lgtseek
rm -r /tmp/lgtseek-master
rm /tmp/master.zip
