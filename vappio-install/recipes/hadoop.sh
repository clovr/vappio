#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

sudo add-apt-repository "deb http://archive.cloudera.com/debian lucid-cdh3 contrib"
sudo add-apt-repository "deb-src http://archive.cloudera.com/debian lucid-cdh3 contrib"
curl -s http://archive.cloudera.com/debian/archive.key | sudo apt-key add -
sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
sudo apt-get update
echo sun-java6-jre shared/accepted-sun-dlj-v1-1 select true | /usr/bin/debconf-set-selections

sudo apt-get  --force-yes -y install sun-java6-jdk
#sudo update-java-alternatives -s java-6-sun
#apt-get -y install hadoop hadoop-datanode hadoop-jobtracker hadoop-namenode hadoop-native hadoop-tasktracker hadoop-sbin
wget -P /tmp http://www.carfab.com/apachesoftware//hadoop/core/hadoop-0.20.2/hadoop-0.20.2.tar.gz
(cd /opt/ && tar -zxvf /tmp/hadoop-0.20.2.tar.gz)
ln -f -s /opt/hadoop-0.20.2 /opt/hadoop
rm /tmp/hadoop-0.20.2.tar.gz

source /opt/vappio-scripts/clovrEnv.sh
checkoutObject.py vappio img-conf/etc/hadoop/conf/core-site.xml.tmpl /opt/hadoop/conf/core-site.xml.tmpl
checkoutObject.py vappio img-conf/etc/hadoop/conf/hdfs-site.xml.tmpl /opt/hadoop/conf/hdfs-site.xml.tmpl
checkoutObject.py vappio img-conf/etc/hadoop/conf/mapred-site.xml.tmpl /opt/hadoop/conf/mapred-site.xml.tmpl

