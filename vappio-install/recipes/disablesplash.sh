#!/bin/bash

rename -f 's/plymouth(\S*)\.conf/plymouth$1.conf.disabled/' /etc/init/plymouth*.conf
apt-get remove plymouth-theme-ubuntu-text
