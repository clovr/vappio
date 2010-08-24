#!/bin/bash

apt-get --force-yes -y install ganglia-monitor
apt-get --force-yes -y install ganglia-webfrontend

ln -f -s /etc/ganglia-webfrontend/apache.conf /etc/apache2/sites-available/ganglia
ln -f -s /etc/apache2/sites-available/ganglia /etc/apache2/sites-enabled/ganglia

#cat /etc/ganglia-webfrontend/apache.conf
#Alias /ganglia /usr/share/ganglia-webfrontend
#add to /etc/apache2/sites-available/default

#update-rc.d -f ganglia-monitor remove
#update-rc.d -f gmetad remove

perl -pi -e 's/memory_limit.*/memory_limit = 1024M/' /etc/php5/apache2/php.ini
perl -pi -e 's/max_execution_time.*/max_execution_time = 180/' /etc/php5/apache2/php.ini
perl -pi -e 's/max_input_time.*/max_input_time = 180/' /etc/php5/apache2/php.ini

/etc/init.d/gmetad stop
/etc/init.d/ganglia-monitor stop
/etc/init.d/apache2 stop

#TODO, missing customizations
#set /etc/ganglia
