#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
curl -s http://archive.cloudera.com/debian/archive.key | sudo apt-key add -
sudo apt-get --force-yes -y install sun-java6-jdk
sudo update-java-alternatives -s java-6-sun
apt-get -y install hadoop
