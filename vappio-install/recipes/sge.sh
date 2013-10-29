#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
apt-get -y install gridengine-common gridengine-client gridengine-master gridengine-exec
/etc/init.d/gridengine-exec stop
/etc/init.d/gridengine-master stop
/etc/init.d/postfix stop
update-rc.d -f gridengine-exec remove
update-rc.d -f gridengine-master remove

echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/init.d/gridengine-exec /etc/init.d/gridengine-exec
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/init.d/gridengine-master /etc/init.d/gridengine-master
