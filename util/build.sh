#!/bin/bash -e

#USAGE: build.sh image.img name1 name2 ... namen
#eg. build.sh clovr_skeleton.img clovr_base clovr_standard

#Takes a skeleton image (image.img) and applies recipes name1 ... namen
#creating one output directory per image
#Assumes to be run on a box that has clovr_build recipe applied
#so utildir and recipedir should already be populated

#TODO run on nightly cron
#echo << . > /etc/init.d/cron.nightly/clovrbuild
##!/bin/bash
#/opt/vappio-util/vp-bootstrap-install
#/opt/vappio-install/recipes/clovr_build
#/opt/vappio-util/build.sh /mnt/image.img clovr_base 
#.
#chmod +x /etc/init.d/cron.nightly/clovrbuild

#for testing on leatherface.igs.umaryland.edu
#mount /dev/sdb1 /mnt
#b=clovr_build
#image=/mnt/image.img
#bname=

mountpoint /mnt
if [ $? != 0 ]
then
    echo "/mnt must be an external mount with sufficient free space. mount this volume first"
    exit 1
fi


recipedir=/opt/vappio-install/bundles
utildir=/opt/vappio-util

image=$1
bname=`basename $image`
namepfx=`echo "$bname" | perl -ne '/(.*)\.\w+/;print $1,"\n"'`

#remaining arguments are recipe names
shift

wget -c -P /mnt http://cb2.igs.umaryland.edu/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
wget -c -P /mnt http://cb2.igs.umaryland.edu/vboxtools-3.2.6.tar.gz
wget -c -P /mnt http://cb2.igs.umaryland.edu/grub-boot.tgz
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/boot /mnt/boot
pushd /mnt
tar cvzf grub-boot.tgz boot
popd
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/util/start_clovr.vmx /mnt/start_clovr.tmpl.vmx
#wget -c -P /mnt http://cb2.igs.umaryland.edu/shared.tgz

defaultname=`date "+%Y%m%d"`

for b in $*
do
    mkdir -p /mnt/$$/$b
    mkdir -p /mnt/$$/$b.live
    currimg=/mnt/$$/$b/$bname
    cp $image $currimg
    devname=`losetup --show -f $currimg`
    mount $devname /mnt/$$/$b.live

    #Set up some things for the chroot jail
    export recipedir=$recipedir
    export b=$b
    mount --bind /proc /mnt/$$/$b.live/proc
    mount --bind /sys /mnt/$$/$b.live/sys
    mount --bind /dev /mnt/$$/$b.live/dev
    #Set up resolv.conf so networking works in chroot
    cp /etc/resolv.conf /mnt/$$/$b.live/etc/resolv.conf
    cp /etc/hostname /mnt/$$/$b.live/etc/hostname
    cp /etc/apt/sources.list.orig /mnt/$$/$b.live/etc/apt/sources.list

    #Apply recipe
    wget -c -P /mnt/$$/$b.live/tmp http://vappio.svn.sourceforge.net/viewvc/vappio/trunk/vappio-install/vp-bootstrap-install
    chroot /mnt/$$/$b.live bash -e /tmp/vp-bootstrap-install
    chroot /mnt/$$/$b.live $recipedir/$b

    #Exit from chroot
    umount /mnt/$$/$b.live/proc
    umount /mnt/$$/$b.live/sys
    umount /mnt/$$/$b.live/dev
    umount /mnt/$$/$b.live
    sync
    losetup -d $devname
    #cleanup img
    /opt/vappio-util/img_run.sh $currimg /opt/vappio-util/cleanupimg
    #releaseCut scripts here

    #Build xen
    #create example clovr-xen.conf and bundle kernel image
    echo "Created $currimg"

    #Build VMware/VBox
    cp $currimg $currimg.vmbundle
    /opt/vappio-util/img_add_tgz.sh $currimg.vmbundle /mnt/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz 
    /opt/vappio-util/img_add_tgz.sh $currimg.vmbundle /mnt/vboxtools-3.2.6.tar.gz
    /opt/vappio-util/img_to_vmdk.sh $currimg.vmbundle /mnt/grub-boot.tgz $currimg.vmdk
    echo "Created $currimg.vmdk"
    mkdir $namepfx
    cd $namepfx
    #Create ovf bundle
    /opt/vappio-util/bundle_ovf.sh $currimg.vmdk $namepfx $namepfx.ovf ~/$namepfx
    #Add vmx file
    /opt/vappio-util/bundle_vmx.sh ".\/$bname.vmdk" /mnt/start_clovr.tmpl.vmx start_clovr.vmx $namepfx
    #Add shared folder 
    svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/mnt/shared shared
    popd
    tar cvzf $namepfx.tgz $namepfx
    #The clouds EC2,Magellan,DIAG should be able to use $currimg
done

