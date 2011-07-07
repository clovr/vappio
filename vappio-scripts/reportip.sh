#!/bin/bash

ipaddr=`/sbin/ifconfig | grep "inet addr" | grep -v "127.0.0.1" | awk '{ print $2 }' | awk -F: '{ print ""$2"" }'`
#update home page
if [ -f /mnt/clovr_home.html.tmpl ]
then
    cat /mnt/clovr_home.html.tmpl | sed -e 's/\$\;IPADDR\$\;/'"$ipaddr"'/g' > /mnt/clovr_home.html
fi
echo $ipaddr > /mnt/vappio-conf/clovr_ip

