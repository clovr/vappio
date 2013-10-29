#!/bin/bash

#Setup hostname
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/hosts.orig /etc/hosts.orig

echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/init.d/hostnamecheck /etc/init.d/hostnamecheck
/etc/init.d/hostnamecheck start

