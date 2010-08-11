#!/bin/bash

ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`

echo "###README###"
echo "Access the CloVR appliance from a web browser at http://$ipaddr"

source /root/clovrEnv.sh

if [ -f /opt/vappio-py/vappio/cli/vmStatus.py ]
then
    /opt/vappio-py/vappio/cli/vmStatus.py
fi
exec bash
