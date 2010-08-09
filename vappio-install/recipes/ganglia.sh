#!/bin/bash

apt-get -y install ganglia-monitor
apt-get -y install ganglia-webfrontend

#cat /etc/ganglia-webfrontend/apache.conf
#Alias /ganglia /usr/share/ganglia-webfrontend
#add to /etc/apache2/sites-available/default
/etc/init.d/apache2 restart
update-rc.d -f ganglia-monitor remove
update-rc.d -f gmetad remove
#TODO update /etc/php5/apache2/php.ini
