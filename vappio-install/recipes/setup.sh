#!/bin/sh

invoke-rc.d apparmor kill
update-rc.d -f apparmor remove
update-rc.d -f x11-common remove
update-rc.d -f landscape-client remove
update-rc.d -f pulseaudio remove
apt-get -y remove landscape-client landscape-common
apt-get -y remove apparmor apparmor-utils apport apport-symptoms ppp pppconfig pppoeconf
apt-get -y remove gsfonts gsfonts-xll
apt-get -y remove wireless-tools wpasupplicant
apt-get -y remove puppet puppet-common puppetmaster
rm /etc/cron.d/cloudinit-updates

apt-get -y install euca2tools
apt-get -y install subversion
apt-get -y install virt-what

rename 's/plymouth(\S+)\.conf/plymouth$1.conf.disabled/' /etc/init/plymouth*.conf
#rename 's/cloud-(\S+)\.conf/cloud-$1.conf.disabled/' /etc/init/cloud-*.conf
