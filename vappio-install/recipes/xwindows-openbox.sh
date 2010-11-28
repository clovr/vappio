#!/bin/bash

apt-get -y install x-window-system
apt-get -y install openbox openbox-themes
apt-get -y install hsetroot

apt-get -y install conky
apt-get -y install tint2
apt-get -y install xwit
apt-get -y install rox-filer

#Install better terminal
apt-get -y install sakura
#Remove annoying sakura - from title bar
perl -pi -e 's/sakura - /         /' /usr/bin/sakura

#/root/.config sakura
tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir -p $tmpdir/root/.config
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.config $tmpdir/root/.config
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd

#Install /etc/xdg
#/etc/xdg/openbox/autostart.sh and tint2 configs
tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir -p $tmpdir/etc/xdg
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/xdg $tmpdir/etc/xdg
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd

#Install /etc/conky
tmpdir=/tmp/$$
rm -rf $tmpdir
mkdir -p $tmpdir/etc/conky
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/conky $tmpdir/etc/conky
pushd $tmpdir
echo "Creating install$$.tgz"
tar cvzf ../install$$.tgz .
echo "Creating install$$.tgz"
tar -C / -xvzf ../install$$.tgz
rm ../install$$.tgz
popd

#Add auto-startup to /etc/profile
#TODO move this to profile.d
echo 'trap "SKIPX=yes" SIGINT' > /tmp/$$.profile
echo 'tty=`who am i | grep "[[:space:]]tty1[[:space:]]"`' >> /tmp/$$.profile
echo 'if [ -z "$DISPLAY" ] && [ "$tty" != "" ]' >> /tmp/$$.profile
echo 'then' >> /tmp/$$.profile
echo 'echo "Starting graphical console. Control-C to abort"' >> /tmp/$$.profile
echo 'sleep 2' >> /tmp/$$.profile
echo 'if [ "$SKIPX" != "yes" ]' >> /tmp/$$.profile
echo 'then' >> /tmp/$$.profile
#Start on tty8
echo '. startx -- :1 >/dev/null 2>&1 &' >> /tmp/$$.profile
echo 'fi' >> /tmp/$$.profile
echo 'fi' >> /tmp/$$.profile
echo 'trap SIGINT' >> /tmp/$$.profile
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/profile /etc/profile
cat /etc/profile >> /tmp/$$.profile
mv /tmp/$$.profile /etc/profile


#apt-get install trayer
#Add clickable links for shared folders
#drop-down menu for vp- API
#apt-get install idesk
#mkdir ~/.idesktop

#Icons for ipaddress, user_data folder, keys folder
#Shutdown, restart, suspend

#logo bottom left
#status, help, URLs right
#icons top left
#ia32-libs needed for firefox


