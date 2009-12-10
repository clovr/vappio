#!/bin/sh

# Get Sun Grid Engine (SGE) settings
source /opt/sge/default/common/settings.sh
 
export PYTHONPATH=/opt/vappio-py
export JAVA_HOME=/usr
  
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/opt/vappio-py/vappio/cli

