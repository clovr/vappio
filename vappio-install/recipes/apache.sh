#!/bin/bash

wget http://cb2.igs.umaryland.edu/clovr_apache_config.tgz
tar -C / -xvzf clovr_apache_config.tgz
/etc/init.d/apache2 restart
