#!/bin/bash

clusters=`cat /tmp/vmStatus.log | perl -ne '/Clusters: (\w+)/;print $1'`

echo -n "Clusters (# instances) : "
for c in $clusters 
do
    if [ "$c" != "local" ]
    then
	num=`vp-describe-clusters --name=$c | grep -c EXEC`
	echo -n "$c($num) ";
    else
	echo -n "$c ";
    fi
done  
echo
instances=`cat /tmp/vmStatus.log | perl -ne '/Instances: (\d+)/;print $1'`
echo -n "Credentials            : "
credentials=`vp-describe-credentials | perl -ne '/CRED\s+(\w+)/;print "$1 "'`
for r in $credentials
do
    if [ "$r" != "local" ]
    then
	echo -n "$r($instances) "
    else
	echo -n "$r "
    fi
done
echo 
