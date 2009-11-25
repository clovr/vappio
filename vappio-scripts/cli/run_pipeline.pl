#!/usr/bin/perl

use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);
use Pod::Usage;

use Config::IniFiles;

my %opts = &parse_options();

## open the log if requested
my $logfh;
if (defined $opts{log}) {
    open($logfh, ">$opts{log}") || die "can't create log file: $!";
}

##
## CODE HERE
##

#Make WS call to retrieve metrics
#Make WS call to run metrics
#Make WS call to run pipeline
#This WS call will create conf file and run
