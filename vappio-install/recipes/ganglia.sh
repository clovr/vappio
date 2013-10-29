#!/bin/bash

apt-get --force-yes -y install ganglia-monitor
apt-get --force-yes -y install ganglia-webfrontend

/etc/init.d/ganglia-monitor stop
/etc/init.d/gmetad stop
/etc/init.d/apache2 stop

update-rc.d -f ganglia-monitor remove
update-rc.d -f gmetad remove

echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/ganglia/gmetad.conf /etc/ganglia/gmetad.conf 
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/ganglia/gmond.conf /etc/ganglia/gmond.conf 

ln -f -s /etc/ganglia-webfrontend/apache.conf /etc/apache2/sites-available/ganglia
ln -f -s /etc/apache2/sites-available/ganglia /etc/apache2/sites-enabled/ganglia

perl -pi -e 's/memory_limit.*/memory_limit = 1024M/' /etc/php5/apache2/php.ini
perl -pi -e 's/max_execution_time.*/max_execution_time = 180/' /etc/php5/apache2/php.ini
perl -pi -e 's/max_input_time.*/max_input_time = 180/' /etc/php5/apache2/php.ini

#start up in /etc/vappio and customizations set in 
#/opt/vappio-scripts/gangliacustoms
