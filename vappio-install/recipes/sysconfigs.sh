#!/bin/bash

etc/profile
etc/sysctl.conf
/etc/pamd.conf/common-session
/root/.profile
/etc/apt/
/etc/security/
/etc/cloud/ #Change /etc/cloud/cloud.cfg:disable_root: 0
/etc/pam.d/
/etc/sysctl.d/

svn export etc
svn export root