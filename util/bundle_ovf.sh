#!/bin/bash

#USAGE: bundle_ovf.sh image.vmdk name output.ovf sharedpath

#Clean up any old vms with the same name
VBoxManage -q unregistervm $2 
VBoxManage -q closemedium $1
VBoxManage -q storageattach $2 --storagectl "IDE Controller" --port 0 --device 0 --type hdd --medium none

rm -rf ~/.VirtualBox/Machines/$2

VBoxManage -q createvm --name $2 --register

VBoxManage -q modifyvm $2 --ostype "Ubuntu_64" --memory 2048 --boot1 disk --nic1 bridged

VBoxManage -q storagectl $2 --name "IDE Controller" --add ide

VBoxManage -q storageattach $2 --storagectl "IDE Controller" --port 0 --device 0 --type hdd --medium $1

#Not certain this is portable
VBoxManage -q modifyvm $2 --nic1 bridged --bridgeadapter1 "en0:Ethernet"

VBoxManage sharedfolder add $2 --name shared --hostpath $4/shared/ 
VBoxManage sharedfolder add $2 --name keys --hostpath $4/keys/ 
VBoxManage sharedfolder add $2 --name user_data --hostpath $4/user_data/
VBoxManage sharedfolder add $2 --name pg_data --hostpath $4/pg_data/

#Create ovf
VBoxManage -q export $2 -o $3
