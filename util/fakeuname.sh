#!/bin/bash

case "$1" in
    '-r')
	`/bin/uname.orig -r`
	;;
    '-m')
	echo "x86_64"
	;;
esac
