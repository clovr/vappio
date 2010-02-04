#!/bin/sh

# Get Sun Grid Engine (SGE) settings
source /opt/sge/default/common/settings.sh
 
export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
export JAVA_HOME=/usr
  
export PATH=$PATH:/usr/local/bin:/usr/local/sbin
export PATH=$PATH:/opt/vappio-py/vappio/cli:/opt/vappio-py/vappio/cli/remote:/opt/vappio-scripts:/opt/vappio-scripts/pipelines
export PATH=$PATH:/opt/crossbow/ec2-local:/opt/crossbow/local:/opt/samtools


##
# These are temporary right now, trying to figure out the best way to 
# allow a cluster to start up its own children
export EC2_HOME=/usr
export EC2_CERT=/root/ec2-cert.pem
export EC2_PRIVATE_KEY=/root/ec2-pk.pem

ulimit -n 8192

