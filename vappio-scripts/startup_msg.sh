#!/bin/bash

ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`

echo "###README###"
echo "Access the CloVR appliance from a web browser at http://$ipaddr"

source /root/clovrEnv.sh

vmStatus.py

exec bash
