#!/bin/bash

pushd /tmp
rm -rf vappio-py
svn export https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-py
export PYTHONPATH=$PYTHONPATH:/tmp/vappio-py
updateAllDirs.py --vappio-scripts --vappio-py --vappio-conf --vappio-py-www --config_policies
popd
rm -rf /tmp/vappio-py
#apache config from other

#install /etc/init.d/vp_cfgapt /etc/init.d/vp_cfgaptec2 /etc/init.d/vp_cfghostname

/etc/init/cloud-*
/etc/init/vappio
/etc/vappio/

#add events for ec2
#pull custom cloud-* with ec2
