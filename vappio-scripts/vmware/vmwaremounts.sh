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
    chmod 777 $shared_mp
# Generic Shared area
    mount -o ttl=3 -t vmhgfs .host:$shared_dir $shared_mp -o uid=33 -o gid=33
    sleep 2

    mkdir -p $userdata_mp
    mkdir -p $keysdir
    mkdir -p $vappioconf_mp
    chmod 777 $userdata_mp
    chmod 777 $keysdir
    chmod 777 $vappioconf_mp

    mount -o ttl=3 -t vmhgfs .host:$userdata_dir $userdata_mp -o uid=33 -o gid=33 -o fmask=000 -o dmask=000
    mount -o ttl=3 -t vmhgfs .host:/keys $keysdir -o uid=33 -o gid=33 -o fmask=077 -o dmask=077
    mount -o ttl=3 -t vmhgfs .host:$vappioconf_dir $vappioconf_mp -o uid=33 -o gid=33 -o fmask=000 -o dmask=000
 
    chmod 777 $shared_mp
    chmod 777 $userdata_mp
    chmod 777 $keysdir
    chmod 777 $vappioconf_mp
}

do_stop() {
    umount $userdata_mp
    umount $keysdir
    umount $vappioconf_mp
    grep "^postgres" /etc/passwd
    if [ $? = 0 ]
    then
    umount $postgres_data_dir_mp
    fi
    umount $shared_mp
    #Clear out udev
    rm -f /etc/udev/rules.d/70-persistent-net.rules
    rm -f /etc/udev/rules.d/70-persistent-cd.rules
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
