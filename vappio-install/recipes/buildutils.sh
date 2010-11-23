#!/bin/bash 

export DEBIAN_FRONTEND=noninteractive

apt-get -y install zip
#Need grub legacy, it just works with xen
#tried grub2 but it is a mess
apt-get -y install grub
#update-grub
apt-get -y install qemu-kvm 

echo "max_loop=128" > /etc/modprobe.d/loop.conf
for ((i=8;i<128;i++)); do
[ -e /dev/loop$i ] || mknod -m 0600 /dev/loop$i b 7 $i
done


#virtualbox utilities, need VBoxManage
#apt-get -y install virtualbox-ose

wget -q http://download.virtualbox.org/virtualbox/debian/oracle_vbox.asc -O- | sudo apt-key add -

sudo add-apt-repository "deb http://download.virtualbox.org/virtualbox/debian lucid non-free"
apt-get update

apt-get -y install virtualbox-3.2
#Install dkms, uninstall
dkms uninstall -m vboxguest -v 3.2.8 || true
dkms uninstall -m vboxvideo -v 3.2.8 || true
dkms uninstall -m vboxsf -v 3.2.8 || true 
dkms uninstall -m vboxnetflt -v 3.2.8 || true 
dkms uninstall -m vboxnetadp -v 3.2.8 || true 
dkms uninstall -m vboxdrv -v 3.2.8 || true

#Retrieve grub and boot sector 
wget -c -P /mnt http://cb2.igs.umaryland.edu/grub-boot.tgz
#Retrive vmware tools
wget -c -P /mnt http://cb2.igs.umaryland.edu/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
#Retrive vmware tools
#wget -c -P /mnt http://cb2.igs.umaryland.edu/vboxtools-3.2.6.tar.gz
wget -c -P /mnt http://cb2.igs.umaryland.edu/VBoxLinuxAdditions-amd64.run

#mkdir -p /opt/opt-packages
svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/opt-packages/ec2-api-tools-1.3-53907/ /opt/opt-packages/ec2-api-tools-1.3-53907/

apt-get install -y ruby
apt-get install -y libruby1.8-extras
pushd /opt
wget http://s3.amazonaws.com/ec2-downloads/ec2-ami-tools.zip
unzip -o ec2-ami-tools.zip
popd

svn export --force https://clovr.svn.sourceforge.net/svnroot/clovr/trunk/opt-packages/ec2-api-tools-1.3-53907/ /opt/opt-packages/ec2-api-tools-1.3-53907/

sudo apt-get -y install apt-cacher apache2 
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/default/apt-cacher /etc/default/apt-cacher

# Install Nimbus stuff
wget -P /tmp http://www.nimbusproject.org/downloads/nimbus-cloud-client-016.tar.gz
tar -C /opt/opt-packages/ -zxvf /tmp/nimbus-cloud-client-016.tar.gz

(cd /opt/opt-packages/nimbus-cloud-client-016 && patch -p1 -i /opt/vappio-install/files/buildutils/clovr-diag.patch)
cp /opt/vappio-install/files/buildutils/b43aa9f3* /opt/opt-packages/nimbus-cloud-client-016/lib/certs
