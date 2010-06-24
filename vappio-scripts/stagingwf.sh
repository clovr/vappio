#!/bin/sh
#
#USAGE: staging.wf.sh [remotehost] [workflow_xml]
#The input workflow XML must the absolute path to a single group from an Ergatis iterator.
#

#This script parse the workflow XML and perform 2 copies
#1)Copy the input files for the group to remotehost. The input files
#  are referenced in a file name $groupnumber.iter

#2)Copy the workflow XML for the group to remotehost.  The workflow
#  XML is contained in a directory g$groupnumber

##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

vlog "###" 
vlog "### $0 aka stagingwf.sh (`whoami`) on `hostname`" 
vlog "###" 

remotehost="$1"
wfxml="$2"

#Stage workflow files
wfcomponentdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.*\/)/);print "$dir1"'`
wfgroupdir=`echo "$wfxml" | perl -ne '($dir1,$dir2) = ($_ =~ /(.*\/)(.*\/.+)\//);print "$dir2"'`
group=`echo "$wfgroupdir" | perl -ne '($group) = ($_ =~ /(g\d+)/);print "$group"'`
vlog "wfxml: $wfxml"
vlog "wfcomponentdir: $wfcomponentdir"
vlog "wfgroupdir: $wfgroupdir"
vlog "group: $group"

#TODO transfer list of files as a single transfer instead of one at a time
vlog "Start transfer of input from $wfgroupdir/$group.iter to $remotehost" 
#Check for $;I_FILE_PATH$;
groupitertype=`cat $wfcomponentdir/$wfgroupdir/$group.iter | grep -v 'I_FILE_PATH'`
if [ "$groupitertype" != "" ]
then
    for f in `cat $wfcomponentdir/$wfgroupdir/$group.iter | grep -v '^\\$' | perl -ne 'split(/\t/);print $_[2],"\n"'`; do
	vlog "Transfering $f to $remotehost:$f" 

	# Commands can't be stored in variables, it just doesn't work w/ the quotes
	# http://www.bash-hackers.org/wiki/doku.php/mirroring/bashfaq/050
	# -R = recursive.  Needed for getting the entire directory tree up to the target file
	# -O = omit directories when preserving times (prevents error when trying to change timestamp of / dirs)
	vlog "CMD: rsync -av -R -O -e \"$ssh_client -i $ssh_key $ssh_options\" $f root@$remotehost:/"
	rsync -av -R -O -e "$ssh_client -i $ssh_key $ssh_options" $f root@$remotehost:/ 1>> $vappio_log 2>> $vappio_log
	if [ $? == 0 ]
	then
	    vlog "rsync success. return value: $?"
	else
	    vlog "ERROR: $0 rsync fail. return value: $?"
	    verror "STAGING WF GROUP $wfcomponentdir/$wfgroupdir/$group.iter FAILURE"
	    exit 1;
	fi
    done 
fi
cd $wfcomponentdir
vlog "Start transfer of workflow xml from $wfcomponentdir/$wfgroupdir to $remotehost:$wfcomponentdir" 
vlog "CMD: rsync -av -R -e \"$ssh_client -i $ssh_key $ssh_options\" *.final.config $wfgroupdir root@$remotehost:$wfcomponentdir" 
rsync -av -R -e "$ssh_client -i $ssh_key $ssh_options" *.final.config $wfgroupdir root@$remotehost:$wfcomponentdir 1>> $vappio_log 2>> $vappio_log
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value: $?"
    verror "STAGING WF XML,CONFIG FAILURE"
    exit 1;
fi

