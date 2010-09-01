#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

sudo add-apt-repository "deb http://archive.cloudera.com/debian lucid-cdh3 contrib"
sudo add-apt-repository "deb-src http://archive.cloudera.com/debian lucid-cdh3 contrib"
curl -s http://archive.cloudera.com/debian/archive.key | sudo apt-key add -
sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
sudo apt-get update
echo sun-java6-jre shared/accepted-sun-dlj-v1-1 select true | /usr/bin/debconf-set-selections

sudo apt-get  --force-yes -y install sun-java6-jdk
#sudo apt-get --force-yes -y install sun-java6-jdk
#sudo update-java-alternatives -s java-6-sun
apt-get -y install hadoop
source /root/clovrEnv.sh
checkoutObject.py vappio img-conf/etc/hadoop/conf/core-site.xml.tmpl /etc/hadoop/conf/core-site.xml.tmpl
checkoutObject.py vappio img-conf/etc/hadoop/conf/hdfs-site.xml.tmpl /etc/hadoop/conf/hdfs-site.xml.tmpl
checkoutObject.py vappio img-conf/etc/hadoop/conf/mapred-site.xml.tmpl /etc/hadoop/conf/mapred-site.xml.tmpl

# svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/hadoop/conf/core-site.xml.tmpl /etc/hadoop/conf/core-site.xml.tmpl
# svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/hadoop/conf/hdfs-site.xml.tmpl /etc/hadoop/conf/hdfs-site.xml.tmpl
# svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/hadoop/conf/mapred-site.xml.tmpl /etc/hadoop/conf/mapred-site.xml.tmpl
