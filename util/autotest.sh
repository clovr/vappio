#!/bin/bash

#Create symlinks in newimages for new builds
#Make sure destination has enough space
#You may need to move your ~/.Virtualbox directory
#eg.
#mv ~/.VirtualBox /data/sangiuoli/.VirtualBox
#ln -s /data/sangiuoli/.VirtualBox ~/.VirtualBox
newimagesdir=/usr/local/projects/clovr/newimages

for imgname `ls $newimagesdir`
do
    VBoxManage list runningvms | grep $imgname
    if [ $? != 0 ]
    then
	#Import and Launch
	VBoxMange import $imgname/$imgname.ovf
	#Launch
	VBoxHeadless --startvm $imgname --vrdp=off
	#Set up shared folders
	
	#Read shared/clovr_ip and announce
done