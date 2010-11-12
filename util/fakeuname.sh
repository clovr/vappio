#!/bin/bash

case "$1" in
    '-r')
	echo "2.6.32-23-generic"
	;;
    '-m')
	echo "x86_64"
	;;
    *)
	echo "Linux"
	;;
esac
