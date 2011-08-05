#!/bin/bash

export BIOINF_HOME=/opt/opt-packages/bioinf-v1r4b1/
export RDP_JAR_PATH=/opt/rdp_classifier/rdp_classifier-2.0.jar

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:/opt/vappio-twisted:$VAPPIO_HOME/vappio-py:$BIOINF_HOME/Denoiser/:$BIOINF_HOME/PyNAST/lib/:$BIOINF_HOME/qiime/lib/
export JAVA_HOME=/usr/lib/jvm/java-6-openjdk/
  
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/usr/sbin
export PATH=$PATH:/opt/vappio-py/vappio/cli:/opt/vappio-py/vappio/cli/remote:/opt/vappio-scripts:/opt/vappio-scripts/pipelines:/opt/vappio-util
export PATH=$PATH:/opt/crossbow:/opt/crossbow/bin:/opt/samtools:/opt/cufflinks:/opt/bowtie
export PATH=$PATH:/opt/hadoop/bin
export PATH=$PATH:/opt/cdhit/:/opt/fasttree:/opt/rdp_classifier:/opt/uclust/:/opt/muscle/:/opt/mafft/bin/:$BIOINF_HOME/PyNAST/bin/:$BIOINF_HOME/qiime/bin/:$BIOINF_HOME/mothur/:$BIOINF_HOME/microbiomeutil/ChimeraSlayer/
export PATH=$PATH:/opt/sratoolkit/
##
# mugsy install
export MUGSY_INSTALL=/opt/mugsy_x86-64
export PATH=$PATH:$MUGSY_INSTALL:$MUGSY_INSTALL/mapping
export PERL5LIB=$MUGSY_INSTALL/perllibs

##
# Something weird for mongodb
export PYTHON_EGG_CACHE=/tmp/python-eggs

## Qiime needs the an env variable set to point to the
## .qiime_config file
export QIIME_CONFIG_FP=$BIOINF_HOME/qiime/.qiime_config

## Qiime needs the BLASTMAT env set
export BLASTMAT=/usr/share/ncbi/data/

## Cunningham 
export PATH=$PATH:/opt/cunningham

## Crossbow environmental variables
export CROSSBOW_HOME=/opt/crossbow

##
# These are temporary right now, trying to figure out the best way to 
# allow a cluster to start up its own children
export EC2_HOME=/opt/ec2-api-tools-1.3

##
# EC2 api stuff needs to go in begining of path to override what is already on the VM
export PATH=$EC2_HOME/bin:$PATH

##
# These environmental varibales are required for hadoop to run without any errors
export HADOOP_NAMENODE_USER=www-data
export HADOOP_DATANODE_USER=www-data

##
# Gbrowse needs the SAMTOOLS env variable set 
export SAMTOOLS=/opt/opt-packages/samtools-0.1.7.5

#Globus perl5lib is causing problems. This will be deactivated until
#it works, see task 376.

#export GLOBUS_LOCATION=/opt/opt-packages/globus-5.0.0
#source $GLOBUS_LOCATION/etc/globus-user-env.sh

# Needed for install-cert when using Nimbus
export PATH=/opt/install-cert:$PATH

#ulimit -n 1000000

clovrWrapper () { date=`date +%Y%m%d%s`;pipelinename=`echo "clovr_$date"`;taskname=`vp-run-pipeline --pipeline-config=$1 -t` && vp-describe-task --block --show --show-error $taskname; }
clovrSleep () { clovrWrapper $1 ; }
clovr16S () { clovrWrapper $1 ; }
clovrMicrobe () { clovrWrapper $1 ; }
clovrMetagenomics () { clovrWrapper $1 ; }
clovrSearch () { clovrWrapper $1 ; }
clovrSleep () { clovrWrapper $1 ; }
 
