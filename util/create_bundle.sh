#!/bin/bash
#Packages a raw disk image as a vmdk for VMware and VirtualBox
USAGE="vp-bundle-release image.img name"

currimg=$1
namepfx=$2

wget -c -P /mnt http://cb2.igs.umaryland.edu/grub-boot.tgz
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/boot /mnt/boot
pushd /mnt
tar cvzf grub-boot.tgz boot
popd

cp --sparse=always $currimg $currimg.vmbundle
/opt/vappio-util/img_run.sh $currimg.vmbundle /opt/vappio-install/recipes/vmware.sh
/opt/vappio-util/img_run.sh $currimg.vmbundle /opt/vappio-install/recipes/vbox.sh
/opt/vappio-util/img_to_vmdk.sh $currimg.vmbundle /mnt/grub-boot.tgz $currimg.vmdk
echo "Created $currimg.vmdk"
mkdir $namepfx
chmod 777 $namepfx
pushd $namepfx
#Create ovf bundle
/opt/vappio-util/bundle_ovf.sh $currimg.vmdk $namepfx $namepfx.ovf ~/$namepfx
#Add vmx file
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/util/start_clovr.vmx /mnt/start_clovr.tmpl.vmx
/opt/vappio-util/bundle_vmx.sh ".\/$namepfx.vmdk" /mnt/start_clovr.tmpl.vmx start_clovr.vmx $namepfx
#Add shared folder 
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/mnt/shared shared
chmod 777 shared
mkdir keys
chmod 777 keys
mkdir user_data
chmod 777 user_data
popd
#The OVF export will create a vmdk file but VMware 
#will not mount rw and throws write errors, ata1 drdy err indf
echo "Moving $currimg.vmdk $namepfx/$namepfx.vmdk"
mv $currimg.vmdk $namepfx/$namepfx.vmdk
currimgbname=`basename $currimg`
rm $namepfx/$currimgbname.vmdk

perl -pi -e "s/href=\".*\.vmdk\"/href=\"$namepfx.vmdk\"/" $namepfx/$namepfx.ovf
chmod 777 $namepfx
#Manifest file may cause problems on import
rm -f $namepfx/$namepfx.mf
sync

#Need to ignore errors from tar due to sparse files
tar -S -cvzf $namepfx.tgz $namepfx || true

#Zip does not support large files and 7z does not preserve file permissions
#zip -r $namepfx.zip $namepfx