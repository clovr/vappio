#!/bin/bash

wget -P /tmp http://www.nimbusproject.org/downloads/install-cert-1.tar.gz
tar -C /opt -zxvf /tmp/install-cert-1.tar.gz
rm /tmp/install-cert-1.tar.gz

wget -P /tmp http://s3.amazonaws.com/ec2-downloads/ec2-api-tools-1.3-57419.zip
(cd /opt && unzip /tmp/ec2-api-tools-1.3-57419.zip)
rm /tmp/ec2-api-tools-1.3-57419.zip

