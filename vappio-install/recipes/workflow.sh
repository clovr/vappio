#!/bin/bash
wget http://cb2.igs.umaryland.edu/wf_clovr.tgz
wget http://cb2.igs.umaryland.edu/drmaa.jar
tar -C / -xvzf wf_clovr.tgz
chmod 777 /opt/workflow-sforge/idfile
chown www-data:www-data /opt/workflow-sforge/idfile
SGE_ROOT=/var/lib/gridengine
mkdir $SGE_ROOT/lib
cp drmaa.jar $SGE_ROOT/lib
cp drmaa.jar /opt/workflow-sforge/jars/
#modify switch.sh for dramma.jar
#modify sge_submitter.sh /opt/workflow-sforge/bin/sge_submitter.sh

perl -pi -e 's/export SGE_ROOT=.*/export SGE_ROOT=\/var\/lib\/gridengine/' /opt/workflow-sforge/bin/sge_submitter.sh
perl -pi -e 's/export SGE_ARCH=.*/export SGE_ARCH=lx26-ia64/' /opt/workflow-sforge/bin/sge_submitter.sh
perl -pi -e 's/\/opt\/sge/\/\/opt\/workflow-sforge\/jars\/drmaa.jar\:/\/var\/lib\/gridengine/' /opt/workflow-sforge/switch.sh
#export SGE_CELL=default
#export SGE_QMASTER_PORT=6444
#export SGE_EXECD_PORT=6445



#Workflow, sge user config
#adduser --quiet --disabled-password --disabled-login guest
mkdir /home/www-data
chown www-data:www-data /home/www-data
chmod 755 /home/www-data
#in /etc/passwd
perl -pi -e 's/^www-data.*/www-data:x:33:33:www-data:\/home\/www-data:\/bin\/bash/' /etc/passwd
