#!/bin/bash

apt-get install ganglia-monitor
apt-get install ganglia-webfrontend
cat /etc/ganglia-webfrontend/apache.conf
Alias /ganglia /usr/share/ganglia-webfrontend
#add to /etc/apache2/sites-available/default
/etc/init.d/apache restart
update-rc.d -f ganglia-monitor remove
update-rc.d -f gmetad remove
/etc/php5/apache2/php.ini
