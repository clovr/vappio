#!/bin/bash

export DEBIAN_FRONTEND=noninteractive


sudo add-apt-repository "deb http://archive.cloudera.com/debian lucid-cdh3 contrib"
sudo add-apt-repository "deb-src http://archive.cloudera.com/debian lucid-cdh3 contrib"
curl -s http://archive.cloudera.com/debian/archive.key | sudo apt-key add -
sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
sudo apt-get update
sudo apt-get  --force-yes -y install sun-java6-jdk
#sudo apt-get --force-yes -y install sun-java6-jdk
#sudo update-java-alternatives -s java-6-sun
apt-get -y install hadoop
