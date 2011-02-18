#!/bin/bash

# Need to setup our NODE_PATH env here so that nodejs knows where the npm
# installed modules are
export NODE_PATH=/opt/npm/

case "$1" in
    start)
	cd /opt/shockandawe/AWE/
	/opt/nodejs/bin/node /opt/shockandawe/AWE/AWE.js > /tmp/awe.log & echo $! > /tmp/awe.pid
	;;
    stop)
	kill `cat /tmp/awe.pid`
	;;
    reload)
	$0 stop
	$0 start
	;;
    *)
	echo "Unknown option"
	exit 1
	;;
esac

exit 0
