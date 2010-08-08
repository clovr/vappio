#!/bin/bash

apt-get -y install daemon gcj-4.4-base gcj-4.4-jre-headless gcj-4.4-jre-lib libgcj-common libgcj10
wget -O /tmp/key http://hudson-ci.org/debian/hudson-ci.org.key
sudo apt-key add /tmp/key
wget -O /tmp/hudson.deb http://hudson-ci.org/latest/debian/hudson.deb
sudo dpkg --install /tmp/hudson.deb
#TODO Change port to 8888 /etc/default/hudson
#Change config to bash, autoenable refresh
#$SU $HUDSON_USER --shell=/bin/bash -c "$DAEMON $DAEMON_ARGS -- $JAVA $JAVA_ARGS -jar $HUDSON_WAR $HUDSON_ARGS"
#Add file /var/lib/hudson/config.xml
update-rc.d -f hudson remove
#find /etc/rc*/ -type l -name *hudson* -exec rm {} \;
source /root/clovrEnv.sh
adduser --quiet --disabled-password --disabled-login hudson --gecos ""
updateAllDirs.py --hudson



