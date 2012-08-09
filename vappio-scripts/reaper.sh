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
echo -n "REAPER " 
date
myhostname=`hostname -f`
echo "Checking for dead hosts"
deadhosts1=`$SGE_ROOT/bin/$ARCH/qhost -q -j -xml | xpath -e "//queue/queuevalue[@name='state_string'][contains(text(),'u')]/../../@name" | perl -ne '($host) = ($_ =~ /name="(.*)"/);print $host," " if ($host)' | sort -u`
if [ "$deadhosts1" != "" ]
then
    echo "Found dead host(s)..."
    $SGE_ROOT/bin/$ARCH/qhost -q -j -xml | xpath -e "//queue/queuevalue[@name='state_string'][contains(text(),'u')]/../../@name"
fi

#
for deadhostname in $deadhosts1
do
    if [ "$deadhostname" == "$myhostname" ]
    then
	verror "Reaper detected self ($deadhostname) as unresponsive, ignoring"
    else
	verror "Unresponsive host $deadhostname"
	vlog "Running remove_sgehost on $deadhostname"
	echo "Running remove_sgehost on $deadhostname"
	$vappio_scripts/remove_sgehost.sh $deadhostname
	vlog "Running vp-terminate-instances on $deadhostname"
	echo "Running vp-terminate-instances on $deadhostname"    
	vp-terminate-instances -t --by=private_dns $deadhostname
    fi
done

#Clear all error states, task #315
#Disabling, to avoid unintentional rescheduling of bad responding DIAG hosts
#qmod -cj '*'
#qmod -cq '*'
#Check for error state and reschedule
execqerror=`qstat -qs E -q exec.q -explain E`
if [ "$execqerror" != "" ]
then
    verror "Resetting exec.q error state: $execqerror"
    qmod -cq exec.q
fi

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
