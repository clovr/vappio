#!/bin/bash

case "$1" in
    '-r')
	echo "2.6.38-12-server"
	;;
    '-m')
	echo "x86_64"
	;;
    *)
	echo "Linux"
	;;
esac
