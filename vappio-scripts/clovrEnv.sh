#!/bin/sh

# Get Sun Grid Engine (SGE) settings
source /opt/sge/default/common/settings.sh

export BIOINF_HOME=/opt/opt-packages/bioinf-v1r4b1/
export RDP_JAR_PATH=$BIOINF_HOME/rdp_classifier/rdp_classifier-2.0.jar

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py:$BIOINF_HOME/Denoiser/:$BIOINF_HOME/PyNAST/:$BIOINF_HOME/Qiime/lib/
export JAVA_HOME=/usr
  
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/usr/sbin
export PATH=$PATH:/opt/vappio-py/vappio/cli:/opt/vappio-py/vappio/cli/remote:/opt/vappio-scripts:/opt/vappio-scripts/pipelines
export PATH=$PATH:/opt/crossbow/ec2-local:/opt/crossbow/local:/opt/samtools:/opt/cufflinks
export PATH=$PATH:$BIOINF_HOME/cd-hit/:$BIOINF_HOME/FastTree:$BIOINF_HOME/rdp_classifier:$BIOINF_HOME/UCLUST/

##
# Something weird for mongodb
export PYTHON_EGG_CACHE=/tmp/python-eggs

##
# These are temporary right now, trying to figure out the best way to 
# allow a cluster to start up its own children
export EC2_HOME=/usr
export EC2_CERT=/tmp/ec2-cert.pem
export EC2_PRIVATE_KEY=/tmp/ec2-pk.pem

ulimit -n 8192

export GLOBUS_LOCATION=/opt/opt-packages/globus-5.0.0
source $GLOBUS_LOCATION/etc/globus-user-env.sh
