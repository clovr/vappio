#!/bin/sh

### Import Vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
###

vlog "###"
vlog "### $0 (`whoami`) on `hostname`"
vlog "###"

dir=$1
masterhost=`cat /mnt/clovr/runtime/master_node`
exechost=`hostname`

# Harvest output
vlog "Harvesting output from $exechost:$dir to $masterhost:$dir"
vlog "CMD: $SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $harvestingq $vappio_scripts/harvesting.sh $exechost $dir"
qsub_cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync y -q $harvestingq $vappio_scripts/harvesting.sh $exechost $dir"
$qsub_cmd 1>> $vappio_log 2>> $vappio_log
vlog "qsub return value: $?"
