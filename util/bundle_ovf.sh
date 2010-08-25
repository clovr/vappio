#!/bin/bash

#USAGE: bundle_ovf.sh image.vmdk name output.ovf sharedpath

VBoxManage -q createvm --name $2 --register

VBoxManage -q modifyvm $2 --ostype "Ubuntu_64" --memory 2048 --boot1 disk --nic1 bridged

VBoxManage -q storagectl $2 --name "IDE Controller" --add ide

VBoxManage -q storageattach $2 --storagectl "IDE Controller" --port 0 --device 0 --type hdd --medium $1

#Not certain this is portable
VBoxManage -q modifyvm $2 --nic1 bridged --bridgeadapter1 "en0:Ethernet"

VBoxManage -q sharedfolder add $2 --name shared --hostpath $4/shared/ 
VBoxManage -q sharedfolder add $2 --name keys --hostpath $4/keys/ 
VBoxManage -q sharedfolder add $2 --name user_data --hostpath $4/user_data/
VBoxManage -q sharedfolder add $2 --name pg_data --hostpath $4/pg_data/

#The OVF export will create the vmdk file
VBoxManage -q export $2 -o $3
#Manifest file causes problems on import
rm -f $3.mf