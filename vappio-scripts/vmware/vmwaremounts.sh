#!/bin/bash

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/vmware/vmware_config.sh

do_start() {
    chmod 777 /tmp
    mkdir -p $shared_mp
    mkdir -p $userdata_mp
    mkdir -p $keysdir
    chmod 777 $userdata_mp
    chmod 777 $shared_mp
    chmod 777 $keysdir
# Generic Shared area
    mount -o ttl=3 -t vmhgfs .host:$shared_dir $shared_mp -o uid=33 -o gid=33
    sleep 2
    mount -o ttl=3 -t vmhgfs .host:$userdata_dir $userdata_mp -o uid=33 -o gid=33 -o fmask=000 -o dmask=000
    mount -o ttl=3 -t vmhgfs .host:/keys $keysdir -o uid=33 -o gid=33 -o fmask=077 -o dmask=077
    chmod 777 $shared_mp
    chmod 777 $userdata_mp
    chmod 777 $keysdir

    
    grep "^postgres" /etc/passwd
    if [ $? = 0 ]
    then
# Postgres specific shared area
	mkdir -p $postgres_data_dir_mp
	mount -o ttl=3 -t vmhgfs .host:$postgres_data_dir $postgres_data_dir_mp -o uid=$postgres_uid
    fi
}

do_stop() {
    umount $shared_mp
    umount $userdata_mp
    umount $keysdir
    grep "^postgres" /etc/passwd
    if [ $? = 0 ]
    then
	umount $postgres_data_dir_mp
    fi
}

case "$1" in
    start)
	do_start
	;;
    stop)
	do_stop
	;;
    restart)
	echo "Skipping restart"
	;;
    *)
	echo $"Usage: $0 {start|stop}"
	exit 1
esac