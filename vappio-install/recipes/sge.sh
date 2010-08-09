#!/bin/bash

#TODO make non-interactive
apt-get -y install gridengine-common gridengine-client gridengine-master gridengine-exec
update-rc.d -f gridengine-exec remove
update-rc.d -f gridengine-master remove
