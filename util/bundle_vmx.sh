#!/bin/bash

#USAGE: ./bundle_vmx.sh image.vmdk template.vmx output.vmx [display_name]
#Default display_name is clovr

#Install
vmdk=$1
name=$4
if [ "$name" = "" ]
then
    name="clovr"
fi
cp $2 $3
perl -pi -e "s/\;NAME\;/$name/g" $3
perl -pi -e "s/\;VMDK\;/$vmdk/g" $3
