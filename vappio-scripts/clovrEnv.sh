#!/bin/sh

# Get Sun Grid Engine (SGE) settings
source /opt/sge/default/common/settings.sh

export BIOINF_HOME=/opt/opt-packages/bioinf-v1r4b1/
export RDP_JAR_PATH=$BIOINF_HOME/rdp_classifier/rdp_classifier-2.0.jar

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py:$BIOINF_HOME/Denoiser/:$BIOINF_HOME/PyNAST/lib/:$BIOINF_HOME/qiime/lib/
export JAVA_HOME=/usr
  
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/usr/sbin
export PATH=$PATH:/opt/vappio-py/vappio/cli:/opt/vappio-py/vappio/cli/remote:/opt/vappio-scripts:/opt/vappio-scripts/pipelines
export PATH=$PATH:/opt/crossbow/ec2-local:/opt/crossbow/local:/opt/samtools:/opt/cufflinks:/opt/opt-packages/bowtie-0.12.0
export PATH=$PATH:/opt/opt-packages/hadoop-0.20.1/bin/
export PATH=$PATH:$BIOINF_HOME/cd-hit/:$BIOINF_HOME/FastTree:$BIOINF_HOME/rdp_classifier:$BIOINF_HOME/UCLUST/:$BIOINF_HOME/MUSCLE/:$BIOINF_HOME/mafft/bin/:$BIOINF_HOME/PyNAST/bin/:$BIOINF_HOME/qiime/bin/:$BIOINF_HOME/mothur/:$BIOINF_HOME/microbiomeutil/ChimeraSlayer/

##
# Something weird for mongodb
export PYTHON_EGG_CACHE=/tmp/python-eggs

## Qiime needs the an env variable set to point to the
## .qiime_config file
export QIIME_CONFIG_FP=$BIOINF_HOME/qiime/.qiime_config

## Qiime needs the BLASTMAT env set
export BLASTMAT=/usr/share/ncbi/data/

##
# These are temporary right now, trying to figure out the best way to 
# allow a cluster to start up its own children
export EC2_HOME=/usr
export EC2_CERT=/tmp/ec2-cert.pem
export EC2_PRIVATE_KEY=/tmp/ec2-pk.pem

ulimit -n 8192

#Globus perl5lib is causing problems. This will be deactivated until
#it works, see task 376.

#export GLOBUS_LOCATION=/opt/opt-packages/globus-5.0.0
#source $GLOBUS_LOCATION/etc/globus-user-env.sh

clovrWrapper () { runPipeline.py --pipeline clovr_wrapper --pipeline-name
clovr_wrapper$$ -- --CONFIG_FILE=$1 ; }
clovr16S () { clovrWrapper $1 ; }
clovrMicrobe () { clovrWrapper $1 ; }
clovrMetagenomics () { clovrWrapper $1 ; }
clovrSearch () { clovrWrapper $1 ; }
