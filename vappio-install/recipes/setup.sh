#!/bin/sh

export DEBIAN_FRONTEND=noninteractive

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

rm -f /etc/cron.d/cloudinit-updates

apt-get -y install euca2ools
apt-get -y install subversion
apt-get -y install virt-what

rename 's/plymouth(\S*)\.conf/plymouth$1.conf.disabled/' /etc/init/plymouth*.conf
rename 's/cloud-(\S*)\.conf/cloud-$1.conf.disabled/' /etc/init/cloud-*.conf

#These are causing non-cloud boots to hang
if [ -f /etc/init/mountall-net.conf ]
then
    mv -f /etc/init/mountall-net.conf /etc/init/mountall-net.conf.disabled
fi
if [ -f /etc/init/mountall-shell.conf ]
then
    mv -f /etc/init/mountall-shell.conf /etc/init/mountall-shell.conf.disabled
fi


svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/fstab /etc/fstab.orig