#!/bin/bash

rename -f 's/plymouth(\S*)\.conf/plymouth$1.conf.disabled/' /etc/init/plymouth*.conf
apt-get -y remove plymouth-theme-ubuntu-text
