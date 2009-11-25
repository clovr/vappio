#!/bin/sh
##
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##
##
vlog "###" 
vlog "### $0 (`whoami`)" 
vlog "###" 

hostname=`hostname -f`

#exechost=$1
vlog "Submitting qsub command"
cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync n -q $repositoryq $vappio_scripts/syncrepository.sh $hostname"
vlog "CMD: $cmd"
$cmd 1>> $vappio_log 2>> $vappio_log
