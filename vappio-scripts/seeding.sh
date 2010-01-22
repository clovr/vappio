#!/bin/sh
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

remotehost=$1
queue=$2

#Stage data
vlog "Running staging for $remotehost"
$staging_script $remotehost 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    vlog "staging successful"
    #Add to proper staging q 
    vlog "Adding $remotehost to $queue"
    $SGE_ROOT/bin/$ARCH/qconf -aattr queue hostlist $remotehost $queue 
else
    vlog "ERROR: $0 staging fail. return value $?"
    verror("SEEDING FAILURE");
    exit 1
fi

