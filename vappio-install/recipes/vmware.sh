#!/bin/bash


wget -c -P /tmp http://cb2.igs.umaryland.edu/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
tar -C / -xvzf  /tmp/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
wget -c -P /tmp http://cb2.igs.umaryland.edu/grub-boot.tgz
tar -C / -xvzf  /tmp/grub-boot.tgz