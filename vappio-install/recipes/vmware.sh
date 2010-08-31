#!/bin/bash

wget -c -P /tmp http://cb2.igs.umaryland.edu/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz
tar -C / -xvzf /tmp/vmware-tools.8.4.2.kernel.2.6.32-21-server.tgz

svn export --force  https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/udev/rules.d/99-vmware-scsi-udev.rules /etc/udev/rules.d/99-vmware-scsi-udev.rules 