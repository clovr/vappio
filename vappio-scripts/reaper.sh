#/bin/bash

#reaper.sh 
#Clean up dead hosts. To be run on master

#This is run in cron, avoid overly verbose logs
mirrorlogs=0

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

#Gather list of likely dead hosts from unreachabe state 'u' in SGE
#On testing, we've encountered state combinations including u,du,uo,duo
deadhosts1=`$SGE_ROOT/bin/$ARCH/qhost -q -j -xml | xpath -e "//queue/queuevalue[@name='state_string'][contains(text(),'u')]/../../@name" | perl -ne '($host) = ($_ =~ /name="(.*)"/);print $host," " if ($host)'`

#
for deadhostname in $deadhosts1
do
    $vappio_scripts/remove_sgehost.sh $deadhostname
    vp-terminate-instances --by=$deadhostname
done

#Clear all error states, task #315
qmod -cj '*'
qmod -cq '*'

#Gather list of other exec hosts that are unreachable
#hosts2=`vp-describe-cluster | grep EXEC`
#TODO, loop by line not space
#for execi in $hosts2
#do
#    hostn=`echo $execi | perl -ne 'chomp; split(/\s+/); print "$_[2] "'`
#    isreachable=`printf "kv\nhostname=$hostn\n" | /opt/vappio-metrics/host-is-reachable | grep "reachable=yes"`
    #hostid=`echo $execi | perl -ne 'chomp; split(/\s+/); print "$_[1] "'`
#    if [ "$isreachable" = "" ] 
#    then
#	vp-terminate-instances --by=$deadhostname
#    fi
#done
