#!/bin/bash
#
#USAGE: staging.wf.sh [remotehost] [workflow_xml]
#
#The input workflow XML must the absolute path to Ergatis workflow
#XML, including a single group from an Ergatis iterator.
#
#
#
#This script parses the workflow XML and perform a number of data transfers
#In the case of an Ergatis iterator
#1)Copy the input files for the group to remotehost. The input files
#  are referenced in a file name $groupnumber.iter
#
#2)Copy the workflow XML for the group to remotehost.  The workflow
#  XML is contained in a directory g$groupnumber
#
#In all other cases, simply copy the workflow xml, argument 2 to this script

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
#Reset workflow xml, group must start from the beginning
compljobs=`zcat $wfxml | grep -c "<state>complete"`
vlog "completed jobs:$compljobs"
if [ "$compljobs" -gt 0 ]
then
    vlog "Handling restart of workflow $wfxml with completed jobs"
    wfxmlbname=`basename $wfxml`
    if [ ${wfxmlbname##*.} == "gz" ]
    then
	wfxmlbase=`dirname $wfxml`
	wfxmlfile=`basename $wfxml .gz`
	vlog "Unzipping $wfxml and setting name to ${wfxmlbase}/${wfxmlfile}"
	gunzip "$wfxml"
	wfxml="${wfxmlbase}/${wfxmlfile}"
	dozip=1
    fi
    #Save backup copy
    rm -f $wfxml.$$
    cp -f $wfxml $wfxml.$$
    #Reset DCE spec
    cat $wfxml.$$ | perl -e 'my $in_dcespec=0;while(<STDIN>){if(m|\<dceSpec|){$in_dcespec=1}if(!$in_dcespec){print;}if(m|<\</dceSpec|){$in_dcespec=0;}}' | grep -v -P '^\s+\<host\>' | grep -v -P '^\s+\<port\>' > $wfxml

    vlog "Resetting group xml $wfxml to incomplete"
    perl -pi -e 's/\<state\>complete/<state>incomplete/g' $wfxml
    if [ "$dozip" == 1 ]
    then
	gzip $wfxml
	wfxml="$wfxml.gz"
    fi
fi

vlog "Start transfer of input from $wfgroupdir/$group.iter to $remotehost" 
#Detect if this looks like a workflow iterator and transfer needed files; otherwise just transfer a wfxml
#Check for $;I_FILE_PATH$;, if this exists good indicator we are in an iterator
groupitertype=`cat $wfcomponentdir/$wfgroupdir/$group.iter | grep 'I_FILE_PATH'`
if [ "$groupitertype" != "" ]
then
    vlog "Found files in iterator $wfcomponentdir/$wfgroupdir/$group.iter. Parsing..."
    #TODO transfer list of files as a single transfer instead of one at a time using --file-list
    for f in `cat $wfcomponentdir/$wfgroupdir/$group.iter | grep -v '^\\$' | perl -ne 'split(/\t/);print $_[2],"\n"'`; do
	vlog "Transfering $f to $remotehost:$f" 

	if [ ! -r "$f" ]
	then
	    vlog "ERROR: $f does not exist"
	    verror "STAGING WF FAILURE. FILE DOES NOT EXIST"
	    exit 1;
	fi

	# Commands can't be stored in variables, it just doesn't work w/ the quotes
	# http://www.bash-hackers.org/wiki/doku.php/mirroring/bashfaq/050
	# -R = recursive.  Needed for getting the entire directory tree up to the target file
	# -O = omit directories when preserving times (prevents error when trying to change timestamp of / dirs)
	vlog "CMD: rsync -av -R -O -e \"$ssh_client -i $ssh_key $ssh_options\" $f root@$remotehost:/"
	rsync -av -R -O -e "$ssh_client -i $ssh_key $ssh_options" $f root@$remotehost:/ #1>> $vappio_log 2>> $vappio_log
	if [ $? == 0 ]
	then
	    vlog "rsync success. return value: $?"
	else
	    vlog "ERROR: $0 rsync fail. return value: $?"
	    verror "STAGING WF GROUP $wfcomponentdir/$wfgroupdir/$group.iter FAILURE"
	    exit 1;
	fi
    done 
else
	vlog "No files found for staging in iterator $wfcomponentdir/$wfgroupdir/$group.iter. Skipping group file staging"
	#Just stage workflow xml
	vlog "Transfering $wfxml to $remotehost:$wfxml" 
	vlog "CMD: rsync -av -R -O -e \"$ssh_client -i $ssh_key $ssh_options\" $wfxml root@$remotehost:/"
	if [ ! -r "$wfxml" ]
	then
	    vlog "ERROR: $wfxml does not exist"
	    verror "STAGING WF FAILURE. WORKFLOW XML FILE DOES NOT EXIST"
	    exit 1;
	fi
	rsync -av -R -O -e "$ssh_client -i $ssh_key $ssh_options" $wfxml root@$remotehost:/ 
	if [ $? == 0 ]
	then
	    vlog "rsync success. return value: $?"
	else
	    vlog "ERROR: $0 rsync fail. return value: $?"
	    verror "STAGING WF GROUP $wfcomponentdir/$wfgroupdir/$group.iter FAILURE"
	    exit 1;
	fi
fi

#Stage config file for a workflow iterator
configfiles=`ls $wfcomponentdir/*.final.config`
if [ "$configfiles" = "" ]
then
    wfcomponentdir=`dirname $wfxml`
    configfiles=`ls $wfcomponentdir/*.final.config`
    wfgroupdir=""
    if [ "$configfiles" = "" ]
    then
	vlog "ERROR: Can't find $wfcomponendir/*.final.config"
	verror "STAGING WF CONFIG FAILURE. Can't find $wfcomponendir/*.final.config"
    fi
fi

cd $wfcomponentdir
vlog "Start transfer of workflow xml from $wfcomponentdir/$wfgroupdir to $remotehost:$wfcomponentdir" 
vlog "CMD: rsync -av -R -e \"$ssh_client -i $ssh_key $ssh_options\" *.final.config $wfgroupdir root@$remotehost:$wfcomponentdir" 
rsync -av -R -e "$ssh_client -i $ssh_key $ssh_options" *.final.config $wfgroupdir root@$remotehost:$wfcomponentdir 
if [ $? == 0 ]
then
    vlog "rsync success. return value: $?"
else
    vlog "ERROR: $0 rsync fail. return value: $?"
    verror "STAGING WF CONFIG FAILURE"
    exit 1;
fi

exit 0

