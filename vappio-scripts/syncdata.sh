#!/bin/bash
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
vlog "### $0 aka syncdata.sh (`whoami`) on `hostname`" 
vlog "###" 

#This script should be run on the master
master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`
myhostname=`hostname -f`;

if [ "$master" != "$myhostname" ]; then
    vlog "WARNING: Master is $master but syndata.sh being called on $myhostname"
fi

if [ "$sync" == "y" ]; then
    while [ -e "$vappio_runtime/syncinprogress" ]
      do
      vlog "Sync already in progress";
      verror "SYNC ALREADY IN PROGRESS. Add'l invocation from $myhostname";
      echo "Sync already in progress. Waiting"
      sleep 60
    done
    touch $vappio_runtime/syncinprogress
    vlog "Creating lock file $vappio_runtime/syncinprogress"
fi

stagingnodes=`$vappio_scripts/printqueuehosts.pl $stagingq`
stagingsubnodes=`$vappio_scripts/printqueuehosts.pl $stagingsubq`
execnodes=`$vappio_scripts/printqueuehosts.pl $execq`

#Always keep master in the queue so we have something to start staging
for node in $stagingnodes
do
    if [ "$node" != "$master" ]; then
	vlog "Deleting $node from $stagingq";
	$SGE_ROOT/bin/$ARCH/qmod -d $stagingq@$node
	#$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $node $stagingq 1>> $vappio_log 2>> $vappio_log
    fi
done

#Disable stagingsub queue
for node in $stagingsubnodes
do
    if [ "$node" != "$master" ]; then
	vlog "Deleting $node from $stagingsubq";
	$SGE_ROOT/bin/$ARCH/qmod -d $stagingsubq@$node
	#$SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $node $stagingsubq 1>> $vappio_log 2>> $vappio_log
    fi
done

#Reschedule any staging jobs
stagingjobs=`$SGE_ROOT/bin/$ARCH/qstat -q $stagingq,$stagingsubq -u '*' | perl -ne 's/^\s+//;print' | cut -f 1 -d ' ' | perl -ne 'chomp;if(/(\d+)/){print "$1 "}'`
if [ "$stagingjobs" != "" ]
then
    vlog "WARNING staging jobs running during syncdata. Rescheduling"
    vlog "Rescheduling staging jobs $stagingjobs"
    $SGE_ROOT/bin/$ARCH/qmod -rj $stagingjobs
fi

#seeding.sh runs staging.sh and adds $node back to the proper queue
#seeding will be run on data nodes that are already seeded and 
#idle in stagingq and/or stagingsubq
#Capture job id in the array $jobs, so we can check status
i=0;

for node in $stagingnodes
do
    if [ "$node" != "$master" ]; then
	vlog "Reseeding $node in $stagingq"
	jobid=`$SGE_ROOT/bin/$ARCH/qsub -o $scratch_dir -e scratch_dir -S /bin/sh -b n -q $stagingq $seeding_script $node $stagingq | perl -ne '($jobid) = ($_ =~ /Your job (\d+)/);print $jobid'`
	if [ $jobid ]; then
	    jobs[$i]=$jobid
	    i=`expr $i + 1`
	else
	    vlog "Error submitting seeding job for node $node"
	fi
    fi
done

##
#Consider set of nodes reported in the stagingsub.q and exec.q
#This recovers from the case where staging fails and exec nodes
#are not added to the stagingsub.q
for node in `for h in $stagingsubnodes $execnodes; do echo $h; done | sort -u`
do
    if [ "$node" != "$master" ]; then 
	vlog "Reseeding $node in $stagingsubq"
	jobid=`$SGE_ROOT/bin/$ARCH/qsub -o $scratch_dir -e $scratch_dir -S /bin/sh -b n -q $stagingq,$stagingsubq $seeding_script $node $stagingsubq | perl -ne '($jobid) = ($_ =~ /Your job (\d+)/);print $jobid'`
	if [ $jobid ]; then
	    jobs[$i]=$jobid
	    i=`expr $i + 1`
	else
	    vlog "Error submitting seeding job for node $node"
	fi
    fi
done

##
#If synchronous, loop over all submitted jobs until they are done. Optionally, we could add a timeout here as well
if [ "$sync" == "y" ]; then
    vlog "sync=y. Waiting on job completion. Number of jobs submitted=${#jobs[*]}"
    finishedjobs=0
    #If all jobs are finished, then we are done
    while [ $finishedjobs -ne ${#jobs[*]} ]
      do
      finishedjobs=0
      for job in ${jobs[*]}
	do
	$SGE_ROOT/bin/$ARCH/qstat -j $job > /dev/null 2> /dev/null
        #If return 0, job is still running. Otherwise, jobid is finished (or jobid is bad). Either way, we want to consider the job done
	if [ $? -ne 0 ]; then
	    finishedjobs=`expr $finishedjobs + 1`
	fi
      done
      sleep 3
      vlog "Finished jobs=$finishedjobs. Number of jobs submitted=${#jobs[*]}"
    done
    vlog "Finished removing sync"
    rm $vappio_runtime/syncinprogress
fi

