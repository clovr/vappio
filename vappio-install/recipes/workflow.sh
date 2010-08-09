#!/bin/bash
wget http://cb2.igs.umaryland.edu/wf_clovr.tgz
wget http://cb2.igs.umaryland.edu/drmaa.jar
tar -C / -xvzf wf_clovr.tgz
chmod 777 /opt/workflow-sforge/idfile
chown www-data:www-data /opt/workflow-sforge/idfile
SGE_ROOT=/var/lib/gridengine
mkdir $SGE_ROOT/lib
cp drmaa.jar $SGE_ROOT/lib
#modify sge_submitter.sh /opt/workflow-sforge/bin/sge_submitter.sh

#Workflow, sge user config
#adduser --quiet --disabled-password --disabled-login guest
mkdir /home/www-data
chown www-data:www-data /home/www-data
chmod 755 /home/www-data
#in /etc/passwd
perl -pi -e 's/^www-data.*/www-data:x:33:33:www-data:\/home\/www-data:\/bin\/bash/' /etc/passwd
