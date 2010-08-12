#!/bin/bash
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
masternode=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`

#Only sync if data resides on a DATA_NODE
#If it is already on the master, do nothing
if [ "$hostname" != "$masternode" ]
then
    vlog "Submitting qsub command"
    cmd="$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/bash -b n -sync n -q $repositoryq $vappio_scripts/syncrepository.sh $hostname"
    vlog "CMD: $cmd"
    $cmd 1>> $vappio_log 2>> $vappio_log
else
    vlog "Data harvested to the master, skipping syncrepository.sh"
fi
