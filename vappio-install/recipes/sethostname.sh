#!/bin/bash

#Setup hostname
svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/hosts.orig /etc/hosts.orig

svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init.d/hostnamecheck /etc/init.d/hostnamecheck
/etc/init.d/hostnamecheck start

