#!/bin/bash

if [ -f /etc/init/cloud-init.conf.disabled ]
then
    mv -f /etc/init/cloud-init.conf.disabled /etc/init/cloud-init.conf
fi

if [ -f /etc/init/cloud-config-ssh.conf.disabled ]
then
    mv -f /etc/init/cloud-config-ssh.conf.disabled /etc/init/cloud-config-ssh.conf
fi


echo "cloud_type: auto
user: qiime
disable_root: 0" > /etc/cloud/cloud.cfg
