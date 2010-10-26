#!/usr/bin/perl
# Fetches all the files tagged in the pipeline's TAGS_TO_DOWNLOAD
# Tests whether the file exists and whether any content present
# Dies if any of the above mentioned tests fail
# @author: Mahesh Vangala
#########################################################
use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case bundling);
###############           MAIN      #################
my %options;
my $result = GetOptions(\%options, 'error_log|e:s');
open(STDERR, ">$options{'error_log'}") or die "Error opening the error log, $options{'error_log'}, $!\n" if($options{'error_log'});
my $header = <>;
unless (trim($header) eq 'kv') {
	die "Header must contain 'kv'\n";
}
print STDOUT $header;

checkForEmptyFiles(getTagList());
close STDERR;
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
		elsif($line =~ /output\.(TAGS_TO_DOWNLOAD)\s*=\s*(.+)\s*$/) {
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
	my @emptyFiles;
	my @nonExistingFiles;
	foreach(@$tagList) {
		my $command = "vp-describe-dataset --tag-name=$_";
		open(COMMAND, "$command |") or print STDERR "Error executing the command, $command, $!\n";
		while(my $line = <COMMAND>) {
			if(trim($line) =~ /^FILE\t(.+)$/) {
				unless(-e $1) {
					push @nonExistingFiles, $1;
				}
				elsif(-z $1) {
					push @emptyFiles, $1;
				}
			}
		}
		close COMMAND;
		print STDERR "Error executing the command, $command; Failed with error code: $?\n" if($?);
	}
	
	print STDERR "Empty files found:\n", join("\n",@emptyFiles), "\n" if(@emptyFiles);
        print STDERR "Following file(s) do not exist:\n", join("\n",@nonExistingFiles),"\n" if(@nonExistingFiles);
}
