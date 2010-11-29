#!/bin/bash

clusters=`cat /tmp/vmStatus.log | perl -ne '/Clusters: ([^:]+)/;print $1'`

echo -n "Clusters (# instances) : $clusters"
echo

credentials=`cat /tmp/vmStatus.log | perl -ne '/Credentials: ([^:]+)/;print $1'`
echo -n "Credentials            : $credentials"
echo 
