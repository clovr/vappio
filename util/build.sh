#!/bin/bash -e

USAGE="vp-build image.img bundlename1 name2 ... namen\n
 To cleanup an aborted build run\n 
 vp-build -c image.img"

#
#eg. build.sh clovr_skeleton.img clovr_base clovr_standard
#

#Takes a skeleton image (image.img) and applies recipes name1 ... namen
#creating one output directory per image

#Assumes to be run on a box that already has clovr-build recipe

#Failed builds may leave mounts and loopback devices
#To cleanup, run
#vp-build [-c cleanup bad build] image.img
#To clean up all builds on the box
#find /mnt -name image.img -exec /opt/vappio-util/vp-build -c {} \;

#for testing on leatherface.igs.umaryland.edu
#mount /dev/sdb1 /mnt
#b=clovr_build
#image=/mnt/image.img
#bname=

handlekill() {
    kill `jobs -p` || true
    mounts=`ls -d /mnt/$$/*.live`
    for b in $mounts
    do
	umount $b/proc || true
	umount $b/sys || true
	umount $b/dev || true
	umount -d $b || true
    done
}

while getopts "ch" options; do
  case $options in
    c ) clear=1
	  shift;;
    h ) echo -e $USAGE
	  exit 1;;
    \? ) echo -e $USAGE
         exit 1;;
  esac
done

image=$1

if [ "$image" = "" ]
then
    echo -e $USAGE
    exit 1;
fi

if [ "$clear" = 1 ]
then
    
    echo "Cleaning up build of $image"
    devs=`losetup -j $image | perl -ne 'm|^(/dev/loop\d+)|;print $1,"\n"'`
    for devname in $devs
    do
	mountdir=`df $devname | tail -1 | perl -ne 'split(/\s+/);print join("\t",@_)' | cut -f 6`
	if [ "$mountdir" != "/dev" ]
	then
	    echo "$image mounted as $devname,$mountdir"
	    umount -d $mountdir/dev || true
	    umount -d $mountdir/sys || true
	    umount -d $mountdir/proc || true
	    umount -d $mountdir/ || true
	fi
	losetup -d $devname || true
    done
    exit;

fi

mountpoint /mnt
if [ $? != 0 ]
then
    echo "/mnt must be an external mount with sufficient free space. mount this volume first"
    exit 1
fi

recipedir=/opt/vappio-install/bundles
utildir=/opt/vappio-util


#bname=`basename $image`
#namepfx=`echo "$bname" | perl -ne '/(.*)\.\w+/;print $1,"\n"'`

if [ "$BUILD_ID" != "" ]
then
    defaultname=`echo "$BUILD_ID" | sed 's/_/-/'`
else
    defaultname=`date "+%Y%m%d"`
fi

#remaining arguments are recipe names
shift

#Setup to kill background jobs

trap handlekill SIGINT SIGTERM

for b in $*
do
    namepfx="$b-$defaultname"
    i=1
    while [ -d "$namepfx" ]
    do
	i=`expr $i + 1`;
	namepfx="$b-$defaultname-$i"
    done
    echo "Building $namepfx"
    mkdir -p /mnt/$$/$b
    mkdir -p /mnt/$$/$b.live
    currimg=/mnt/$$/$b/$namepfx.img
    #Copy image
    zfile=`file $image | grep gzip` || true
    if [ "$zfile" != "" ]
    then
        #Zipped sparse files provide faster copy
	image=`tar -C /mnt/$$/$b.live -xvzf $image` || true
	if [ -f "/mnt/$$/$b.live/$image" ]
	then
	    mv /mnt/$$/$b.live/$image $currimg
	else
	    echo "Bad compressed image $image. Can't fine $ibname in output"
	    exit 1
	fi
    else
	echo "Copying $image to $currimg"
	cp --sparse=always $image $currimg
    fi
    devname=`losetup --show -f $currimg`
    mount $devname /mnt/$$/$b.live

    #Set up some things for the chroot jail
    export recipedir=$recipedir
    export b=$b
    mount --bind /proc /mnt/$$/$b.live/proc
    mount --bind /sys /mnt/$$/$b.live/sys
    mount --bind /dev /mnt/$$/$b.live/dev
    touch /mnt/$$/$b.live/var/run/utmp 
    touch /mnt/$$/$b.live/var/run/btmp
    touch /mnt/$$/$b.live/var/run/wtmp
    touch /mnt/$$/$b.live/var/run/lastlog
    chgrp -v utmp /mnt/$$/$b.live/var/run/utmp /mnt/$$/$b.live/var/log/lastlog
    chmod -v 664 /mnt/$$/$b.live/var/run/utmp /mnt/$$/$b.live/var/log/lastlog
    #Set up resolv.conf so networking works in chroot
    cp /etc/resolv.conf /mnt/$$/$b.live/etc/resolv.conf
    cp /etc/hostname /mnt/$$/$b.live/etc/hostname
    cp /etc/apt/sources.list.orig /mnt/$$/$b.live/etc/apt/sources.list
    #Set up apt proxy to speed up downloads
    mkdir -p  /mnt/$$/$b.live/etc/apt.conf.d
    #Check for apt proxy
    curl http://localhost:3142 > /dev/null
    if [ $? = 0 ]
    then
	svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/apt/apt.conf.d/01proxy /mnt/$$/$b.live/etc/apt/apt.conf.d/01proxy
    fi
    #Apply recipe
    wget -c -P /mnt/$$/$b.live/tmp http://vappio.svn.sourceforge.net/viewvc/vappio/trunk/vappio-install/vp-bootstrap-install
    chroot /mnt/$$/$b.live bash -e /tmp/vp-bootstrap-install
    chroot /mnt/$$/$b.live $recipedir/$b
    
    #Remove apt proxy
    rm -f /mnt/$$/$b.live/etc/apt/apt.conf.d/01proxy
    #Reset hostname
    echo -n > /mnt/$$/$b.live/etc/hostname

    mkdir -p /mnt/$$/$b.live/etc/vappio/
    echo "$namepfx" > /mnt/$$/$b.live/etc/vappio/release_name
    echo "$b" > /mnt/$$/$b.live/etc/vappio/bundle_name

    #Exit from chroot
    umount /mnt/$$/$b.live/proc
    umount /mnt/$$/$b.live/sys
    sleep 2
    umount /mnt/$$/$b.live/dev
    sleep 2
    umount /mnt/$$/$b.live
    sync
    losetup -d $devname
    #cleanup img
    echo "Cleaning image $currimg"
    /opt/vappio-util/img_run.sh $currimg /opt/vappio-util/cleanupimg
    #releaseCut scripts here

    #Build xen
    #create example clovr-xen.conf and bundle kernel image
    echo "Created $currimg"

    #Build VMware/VBox
    /opt/vappio-util/create_bundle.sh $currimg $namepfx
    mv $currimg $namepfx.img
    /opt/vappio-util/vp-compress-img $namepfx.img $namepfx.img.tgz || true
done

