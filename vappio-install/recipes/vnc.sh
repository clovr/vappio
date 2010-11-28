#!/bin/bash

#Add vncserver
apt-get -y install x11vnc

#Launch with
#x11vnc -http -forever -xkb -find &