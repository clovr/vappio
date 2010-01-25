#!/bin/sh

# Get Sun Grid Engine (SGE) settings
source /opt/sge/default/common/settings.sh
 
export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
export JAVA_HOME=/usr
  
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/opt/vappio-py/vappio/cli:/opt/vappio-scripts:/opt/vappio-scripts/pipelines:/opt/crossbow/ec2-local:/opt/crossbow/local

export EC2_HOME=/usr

ulimit -n 8192

