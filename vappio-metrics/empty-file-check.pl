#!/usr/bin/perl
# Fetches all the files tagged in the pipeline's TAGS_TO_DOWNLOAD
# Tests whether the file exists and whether any content present
# Dies if any of the above mentioned tests fail
# @author: Mahesh Vangala
#########################################################
use strict;
use warnings;

###############           MAIN      #################
my $header = <>;
unless (trim($header) eq 'kv') {
	die "Header must contain 'kv'\n";
}
print STDOUT $header;

checkForEmptyFiles(getTagList());
exit(0);
###############       END OF MAIN   #################


sub trim {
	my ($param) = @_;
	$param =~ s/^\s+//;
	$param =~ s/\s+$//;
	return $param;
}

sub getTagList {
	my $refHash = {};
	while(my $line = <>) {
		if($line =~ /input\.(PIPELINE_NAME)\s*=\s*(.+)\s*$/) {
			$$refHash{$1} = $2;
		}
		elsif($line =~ /input\.(TAGS_TO_DOWNLOAD)\s*=\s*(.+)\s*$/) {
			$$refHash{$1} = $2;
		}
		print STDOUT $line;
	}
	my $refTagList;
	foreach(split(',',$$refHash{'TAGS_TO_DOWNLOAD'})) {
		push @$refTagList, $$refHash{'PIPELINE_NAME'}.'_'.$_;
	}
	return $refTagList;
}

sub checkForEmptyFiles {
	my ($tagList) = @_;
	foreach(@$tagList) {
		my $command = "vp-describe-dataset --tag-name=$_";
		open(COMMAND, "$command |") or die "Error executing the command, $command, $!\n";
		while(my $line = <COMMAND>) {
			if(trim($line) =~ /^FILE\t(.+)$/) {
				unless(-e $1) {
					die "File, $1, does not exist\n";
				}
				if(-z $1) {
					die "File, $1, has no output written to it\n";
				}
			}
		}
		close COMMAND;
		die "Error executing the command, $command; Failed with error code: $?\n" if($?);
	}	
}
