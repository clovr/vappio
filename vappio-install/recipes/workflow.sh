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
