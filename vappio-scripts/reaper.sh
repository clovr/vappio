#/bin/bash

#reaper.sh 
#Clean up dead hosts. To be run on master

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

#Attempt to ping and ssh hosts up to maxretry

#Gather list of likely dead hosts from unreachabe state 'u'
#On testing, we've encountered state combinations including u,du,uo,duo
deadhosts1=`$SGE_ROOT/bin/$ARCH/qhost -q -j -xml | xpath -e "//queue/queuevalue[@name='state_string'][contains(text(),'u')]/../../@name" | perl -ne '($host) = ($_ =~ /name="(.*)"/);print $host," " if ($host)'`

#
for deadhostname in $deadhosts1
do
  #Disable all queues on this host
  echo "Removing dead host $deadhostname\n"
  $SGE_ROOT/bin/$ARCH/qmod -d "*@$deadhostname"
  #Reschedule any running jobs on this machine
  $SGE_ROOT/bin/$ARCH/qmod -f -rq $execq@$deadhostname
  #Remove any other jobs on this host?

  #Remove host from SGE
  $SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $deadhostname $stagingsubq
  $SGE_ROOT/bin/$ARCH/qconf -dattr queue hostlist $deadhostname $execq
  $SGE_ROOT/bin/$ARCH/qconf -de $deadhostname
  $SGE_ROOT/bin/$ARCH/qconf -ds $deadhostname
  $SGE_ROOT/bin/$ARCH/qconf -kej $deadhostname
  $SGE_ROOT/bin/$ARCH/qconf -dh $deadhostname
done

#Clear all error states, task #315
#qmod -c '*'
