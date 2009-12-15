#!/bin/sh
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

#TODO try seeding the data nodes first
vlog "Start transfer of input from $wfgroupdir/$group.iter to $remotehost" 
for f in `cat $wfcomponentdir/$wfgroupdir/$group.iter | grep -v '^\\$' | perl -ne 'split(/\t/);print $_[2],"\n"'`; do
	vlog "Transfering $f to $remotehost:$f" 

	# Commands can't be stored in variables, it just doesn't work w/ the quotes
	# http://www.bash-hackers.org/wiki/doku.php/mirroring/bashfaq/050
	# -R = recursive.  Needed for getting the entire directory tree up to the target file
	# -O = omit directories when preserving times (prevents error when trying to change timestamp of / dirs)
#	rsync -av -e "$ssh_client -i $ssh_key $ssh_options" $f $remotehost:$f;
	vlog "CMD: rsync -av -R -O -e \"$ssh_client -i $ssh_key $ssh_options\" $f root@$remotehost:/"
	rsync -av -R -O -e "$ssh_client -i $ssh_key $ssh_options" $f root@$remotehost:/ 1>> $vappio_log 2>> $vappio_log
	vlog "rsync return value: $?"
done 
cd $wfcomponentdir
vlog "Start transfer of workflow xml from $wfcomponentdir/$wfgroupdir to $remotehost:$wfcomponentdir" 
#cmd="rsync -av -R -e \"$ssh_client -i $ssh_key $ssh_options\" *.final.config $wfgroupdir root@$remotehost:$wfcomponentdir"
vlog "CMD: rsync -av -R -e \"$ssh_client -i $ssh_key $ssh_options\" *.final.config $wfgroupdir root@$remotehost:$wfcomponentdir" 
rsync -av -R -e "$ssh_client -i $ssh_key $ssh_options" *.final.config $wfgroupdir root@$remotehost:$wfcomponentdir 1>> $vappio_log 2>> $vappio_log
vlog "rsync return value: $?"
