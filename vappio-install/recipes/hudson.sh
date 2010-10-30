#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt-get -y install openjdk-6-jre daemon gcj-4.4-base gcj-4.4-jre-headless gcj-4.4-jre-lib libgcj-common libgcj10
apt-get -y install libxml-xpath-perl
wget --retry-connrefused -O /tmp/key http://hudson-ci.org/debian/hudson-ci.org.key
sudo apt-key add /tmp/key
#Latest is link is broken as of 9/4
#wget -O /tmp/hudson.deb http://hudson-ci.org/latest/debian/hudson.deb
wget --retry-connrefused -O /tmp/hudson.deb http://download.hudson-labs.org/debian/hudson_1.374_all.deb
sudo dpkg --install /tmp/hudson.deb
#Wait in case hudson is starting
sleep 20
if [ -f "/var/run/hudson/hudson.pid" ] && [ "$BUILD_ID" != "" ]
then
    hpid=`cat /var/run/hudson/hudson.pid`
    echo "Hudson pid: $hpid"
    echo "Attempting to stop hudson. Restart Hudson for changes to take effect"
    /etc/init.d/hudson stop
    sleep 5
    echo "Attempting kill of $hpid"
    kill $hpid || true
    sleep 5
fi

perl -pi -e 's/HTTP_PORT=8080/HTTP_PORT=8888/' /etc/default/hudson
perl -pi -e 's/MAXOPENFILES=8192/#MAXOPENFILES=8192/' /etc/default/hudson

#TODO Change config to bash, autoenable refresh
#$SU $HUDSON_USER --shell=/bin/bash -c "$DAEMON $DAEMON_ARGS -- $JAVA $JAVA_ARGS -jar $HUDSON_WAR $HUDSON_ARGS"

update-rc.d -f hudson remove
update-rc.d -f postfix remove
source /opt/vappio-scripts/clovrEnv.sh
#adduser --quiet --disabled-password --disabled-login hudson --gecos ""
updateAllDirs.py --hudson

svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/hudson/hudson-config/config.xml /var/lib/hudson/config.xml

wget -O /var/lib/hudson/plugins/build-timeout.hpi http://hudson-ci.org/latest/build-timeout.hpi

find /var/lib/hudson -type d -exec chmod 777 {} \;
find /var/lib/hudson -type f -exec chmod 666 {} \;
chmod 666 /var/lib/hudson/config.xml
