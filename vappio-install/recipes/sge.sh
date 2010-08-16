#!/bin/bash

export DEBIAN_FRONTEND=noninteractive
#TODO make non-interactive
apt-get -y install gridengine-common gridengine-client gridengine-master gridengine-exec
/etc/init.d/gridengine-exec stop
/etc/init.d/gridengine-master stop
/etc/init.d/postfix stop
update-rc.d -f gridengine-exec remove
update-rc.d -f gridengine-master remove

