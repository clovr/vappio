#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

# Need to delete /etc/hostname to work in diag
rm -f /etc/hostname

#Get clean apt.sources
tmpdir=/tmp/
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/apt $tmpdir/etc/apt
#Make non-EC apt the default
cp $tmpdir/etc/apt/sources.list.orig /etc/apt/sources.list

#Reset hostname
echo -n > /etc/hostname

#Get SVN
apt-get -y install subversion

# More tinkering needed for packer
apt-get -y install python-software-properties

#Set some defaults
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/default/rcS /etc/default/rcS

#Update permissions on /tmp and /mnt
chmod 777 /tmp
chmod 777 /mnt

# Checkout the environment and load it
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/environment /etc/environment
source /etc/environment


#Checkout utils
#TODO, consider moving these elsewhere
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/vappio-py /opt/vappio-py
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/vappio-checkout /etc/vappio-checkout
# Keeping this old style until we are more stable
#checkoutObject.py vappio img-conf/etc/apt/apt.conf.d /etc/apt/apt.conf.d

#Force keeping our custom config files versus overwrite on updates
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/apt/apt.conf.d/05dpkg_forceconfnew /etc/apt/apt.conf.d/05dpkg_forceconfnew

#Default dash shell breaks many shell scripts
ln -sf /bin/bash /bin/sh

#Runlevel on EC2 is 4. Default ubuntu is 2
#Can reset in init/rc-sysinit.conf or inittab
#echo "DEFAULT_RUNLEVEL=4" > /etc/inittab

apt-get -y --force-yes update
#We could automatically upgrade but will make this manual for now
#apt-get -y --force-yes upgrade

#Clean startup process
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

#These should can be removed from here and put elsewhere
apt-get -y install euca2ools
apt-get -y install virt-what
apt-get -y install unzip bzip2 gzip
apt-get -y install screen

#If this is an ec2 vm, disable cloud services by default
rm -f /etc/cron.d/cloudinit-updates
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
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/fstab /etc/fstab.orig

#Set up ntp cron job to update time
apt-get -y install ntpdate
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/init.d/ntpdate.sh /etc/init.d/ntpdate.sh
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/cron.hourly/ntpdate /etc/cron.hourly/ntpdate

#Install default boot loader, can be overwritten later
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/boot /boot
