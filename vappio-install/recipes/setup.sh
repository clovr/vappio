#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/apt $tmpdir/etc/apt
#Make non-EC apt the default
cp /etc/apt/sources.list.orig /etc/apt/sources.list

apt-get -y install subversion

chmod 777 /tmp

# Bootstrap checkoutObject
# Checkout the environment and load it
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/environment /etc/environment
source /etc/environment

svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py /opt/vappio-py
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/vappio-checkout /etc/vappio-checkout

# Keeping this old style until we are more stable
#checkoutObject.py vappio img-conf/etc/apt/apt.conf.d /etc/apt/apt.conf.d
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/apt/apt.conf.d /etc/apt/apt.conf.d/

#Default dash shell breaks many a shell script
ln -sf /bin/bash /bin/sh

#Runlevel on EC2 is 4. 
#Default ubuntu is 2
#Can reset in init/rc-sysinit.conf or inittab
#echo "DEFAULT_RUNLEVEL=4" > /etc/inittab

apt-get -y --force-yes update
apt-get -y --force-yes upgrade

invoke-rc.d apparmor stop
update-rc.d -f apparmor remove
update-rc.d -f x11-common remove
update-rc.d -f landscape-client remove
update-rc.d -f pulseaudio remove
update-rc.d -f ondemand remove

apt-get -y remove landscape-client landscape-common
apt-get -y remove apparmor apparmor-utils apport apport-symptoms ppp pppconfig pppoeconf
apt-get -y remove gsfonts gsfonts-x11
apt-get -y remove wireless-tools wpasupplicant
apt-get -y remove puppet puppet-common puppetmaster
apt-get -y remove avahi-daemon 

#Remove start up messages
rm -f /etc/update-motd.d/51_update-motd
rm -f /etc/update-motd.d/90-updates-available
rm -f /etc/update-motd.d/91-release-upgrade
rm -f /etc/update-motd.d/92-uec-upgrade-available

#Remove unneccessary cron jobs
rm -f /etc/cron.daily/mlocate
rm -f /etc/cron.daily/popularity-contest
rm -f /etc/cron.daily/bsdmainutils
rm -f /etc/cron.monthly/standard

#Disable slow framebuffer
echo "blacklist vga16fb" > /etc/modprobe.d/blacklist-framebuffer.conf

#Add basic help
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/update-motd.d/10-help-text /etc/update-motd.d/10-help-text

rm -f /etc/cron.d/cloudinit-updates

apt-get -y install euca2ools
apt-get -y install virt-what
apt-get -y install unzip bzip2 gzip
apt-get -y install screen

#Disable cloud services by default
rename -f 's/plymouth(\S*)\.conf/plymouth$1.conf.disabled/' /etc/init/plymouth*.conf
rename -f 's/cloud-(\S*)\.conf/cloud-$1.conf.disabled/' /etc/init/cloud-*.conf

#These are causing non-cloud boots to hang
if [ -f /etc/init/mountall-net.conf ]
then
    mv -f /etc/init/mountall-net.conf /etc/init/mountall-net.conf.disabled
fi
if [ -f /etc/init/mountall-shell.conf ]
then
    mv -f /etc/init/mountall-shell.conf /etc/init/mountall-shell.conf.disabled
fi

#Copy virgin fstab so we can boot
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/fstab /etc/fstab.orig

#Set up ntp cron job
apt-get -y install ntpdate
#checkoutObject.py vappio img-conf/etc/init.d/ntpdate.sh /etc/init.d/ntpdate.sh
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init.d/ntpdate.sh /etc/init.d/ntpdate.sh

