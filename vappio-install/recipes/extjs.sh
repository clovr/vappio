#!/bin/bash

# Clear out anything that might be installed already
mkdir /var/www/extjs
rm -rf /var/www/extjs/*

# Download and unpack then copy into  /var/www/
curl -s http://extjs.cachefly.net/ext-3.3.1.zip > /tmp/ext-3.3.1.zip
unzip -q -o /tmp/ext-3.3.1.zip -d /tmp/
cp -r /tmp/ext-3.3.1/* /var/www/extjs/
