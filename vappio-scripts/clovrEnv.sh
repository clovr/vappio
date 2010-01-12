#!/bin/sh

# Get Sun Grid Engine (SGE) settings
source /opt/sge/default/common/settings.sh
 
expoort VAPPIO_HOME=/opt
export PYTHONPATH=/opt/vappio-py
export JAVA_HOME=/usr
  
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/opt/vappio-py/vappio/cli:/opt/vappio-scripts:/opt/vappio-scripts/pipelines:/opt/crossbow/ec2-local:/opt/crossbow/local

ulimit -n 8192

