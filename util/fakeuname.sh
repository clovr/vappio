#!/bin/bash

case "$1" in
    '-r')
	`uname -r`
	;;
    '-m')
	echo "x86_64"
	;;
esac
