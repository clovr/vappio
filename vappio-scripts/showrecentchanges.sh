#!/bin/sh

#Show files that have changed < $1 days ago. This is useful if you want a list of recent changes on image

if [ -z $1 ]
then 
    echo "$0 [days]. Shows files on image in commonly modified directories that have changed < days ago"
    exit
fi

find /opt -path /opt/sge/default -prune -o -path /opt/opt-packages/hadoop-0.20.1/logs -prune -o -mtime -$1 
find /etc/init.d -mtime -$1
find /usr/local/stow -mtime -$1
