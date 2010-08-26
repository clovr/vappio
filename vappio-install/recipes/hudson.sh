#!/bin/bash

export DEBIAN_FRONTEND=noninteractive


apt-get -y install openjdk-6-jre daemon gcj-4.4-base gcj-4.4-jre-headless gcj-4.4-jre-lib libgcj-common libgcj10
apt-gety -y install libxml-xpath-perl
wget -O /tmp/key http://hudson-ci.org/debian/hudson-ci.org.key
sudo apt-key add /tmp/key
wget -O /tmp/hudson.deb http://hudson-ci.org/latest/debian/hudson.deb
sudo dpkg --install /tmp/hudson.deb
/etc/init.d/hudson stop

perl -pi -e 's/HTTP_PORT=8080/HTTP_PORT=8888/' /etc/default/hudson
perl -pi -e 's/MAXOPENFILES=8192/#MAXOPENFILES=8192/' /etc/default/hudson

#TODO Change config to bash, autoenable refresh
#$SU $HUDSON_USER --shell=/bin/bash -c "$DAEMON $DAEMON_ARGS -- $JAVA $JAVA_ARGS -jar $HUDSON_WAR $HUDSON_ARGS"

update-rc.d -f hudson remove
update-rc.d -f postfix remove
source /root/clovrEnv.sh
#adduser --quiet --disabled-password --disabled-login hudson --gecos ""
updateAllDirs.py --hudson

svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/hudson/hudson-config/config.xml /var/lib/hudson/config.xml

find /var/lib/hudson -type d -exec chmod 777 {} \;
find /var/lib/hudson -type f -exec chmod 666 {} \;
chmod 666 /var/lib/hudson/config.xml
