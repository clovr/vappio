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
    $vappio_scripts/remove_sgehost.sh $deadhostname
done

#Clear all error states, task #315
qmod -cj '*'
qmod -cq '*'
