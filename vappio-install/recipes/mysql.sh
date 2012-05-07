#!/bin/sh
apt-get -y install mysql-server

perl -pi -e 's|^datadir\s*=.*|datadir=/mnt/mysql|' /etc/mysql/my.cnf
perl -pi -e 's|^max_allowed_packet\s*=|max_allowed_packet=1000M|'  /etc/mysql/my.cnf

#TODO, need to add directories to app-armor and restart

#TODO, add this to shared scripts
#mkdir /mnt/mysql
#mysql_install_db --datadir=/mnt/mysql
#OR mv /var/lib/mysql/* /mnt/mysql