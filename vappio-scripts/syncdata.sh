#!/bin/sh
#syncdata.sh
#Mirrors the staging directory from the master 
#to the virtualized grid, including DATA_NODES (in staging.q)
#and EXEC_NODES (in stagingsub.q)
#
#First, removes all nodes from the staging queues
#Runs staging script to perform the mirror
#And add nodes back to the staging queues

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##
sync="n"
if [ $1 ]; then
    if [ "$1" == "--synchronous" ]; then
        sync="y"
    fi
fi

vlog "###" 
vlog "### $0 (`whoami`) on `hostname`" 
vlog "###" 

#This script should be run on the master
stagingnodes=`$vappio_scripts/printqueuehosts.pl $stagingq`
stagingsubnodes=`$vappio_scripts/printqueuehosts.pl $stagingsubq`

master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
#Always keep master in the queue so we have something to start staging

for node in $stagingnodes
 do
if [ "$node" != "$master" ]; then
vlog "Deleting $node from $stagingq";
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $node $stagingq 1>> $vappio_log 2>> $vappio_log
fi
done

for node in $stagingsubnodes
 do
if [ "$node" != "$master" ]; then
vlog "Deleting $node from $stagingsubq";
$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $node $stagingsubq 1>> $vappio_log 2>> $vappio_log
fi
done


#seeding.sh runs staging.sh and adds $node back to the proper queue
#seeding will be run on data nodes that are already seeded and 
#idle in stagingq and/or stagingsubq

for node in $stagingnodes
 do
if [ "$node" != "$master" ]; then
vlog "Reseeding $node in $stagingq"
$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync $sync -q $stagingq $seeding_script $node $stagingq 1>> $vappio_log 2>> $vappio_log
fi
done

for node in $stagingsubnodes
 do
if [ "$node" != "$master" ]; then 
vlog "Reseeding $node in $stagingsubq"
$SGE_ROOT/bin/$ARCH/qsub -o /mnt/scratch -e /mnt/scratch -S /bin/sh -b n -sync $sync -q $stagingq,$stagingsubq $seeding_script $node $stagingsubq 1>> $vappio_log 2>> $vappio_log
fi
done
