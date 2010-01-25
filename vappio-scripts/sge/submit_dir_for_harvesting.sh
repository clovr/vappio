#!/bin/sh

### Import Vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
###

vlog "###"
vlog "### $0 (`whoami`) on `hostname`"
vlog "###"

dir=$1
master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
exechost=`hostname -f`

if [ "$exechost" != "$master" ]; then   
    # Harvest output
    vlog "Harvesting output from $exechost:$dir to $master:$dir"
    vlog "CMD: $SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $harvestingq $vappio_scripts/harvesting.sh $exechost $dir"
    qsub_cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $harvestingq $vappio_scripts/harvesting.sh $exechost $dir"
    $qsub_cmd 1>> $vappio_log 2>> $vappio_log
    vlog "qsub return value: $?"

else 
    vlog "Skipping harvesting from master node; master node does not need to harvest to itself."
fi               
