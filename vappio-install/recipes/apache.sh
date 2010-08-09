#!/bin/bash

svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/init.d/apache2 /etc/init.d/apache2

wget http://cb2.igs.umaryland.edu/clovr_apache_config.tgz
tar -C / -xvzf clovr_apache_config.tgz
/etc/init.d/apache2 restart
