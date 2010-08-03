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

# open ini file
my $cfg = new Config::IniFiles( -file => $opts{conf}, 
				-default => 'general',
				-nocase => 0,);

# overwrite config values with anything the user passed in
# todo

my $name = $opts{name};
my $master = $opts{master};

# this is something of a hack as in the future we might want to lock
# down this key to only be usable from within the cloud?
my $ssh_key = $cfg->val('general', 'CLUSTER_PRIVATE_KEY');

my $cloud_type = $cfg->val('general', 'CLOUD_TYPE');

my $staging_dir;

if ($cloud_type eq "EC2") {
    $staging_dir = "/mnt/staging";
}
else {
    $staging_dir = "/mnt/staging";
}

print "Name=$name\n";

foreach my $file (@ARGV) {
    $file =~ s/\/$//; # remove trailing /
    print "Prep $file\n";
}

foreach my $file (@ARGV) {
    my $cmd = "rsync -av -e \"ssh -i $ssh_key\" $file root@".$master.":$staging_dir/$name/"; 
    print  "$cmd\n";
    print `$cmd`;
}


exit(0);

#
# SUBROUTINES
#



sub _log {
    my $msg = shift;

    if ($logfh) {
	print {$logfh} "$msg\n";
    } else {
	print "LOG: $msg\n";
    }
}


sub parse_options {
    my %options = ();
    my $results = GetOptions (\%options, 
			      'conf|c=s',
			      'name|n=s',
			      'master|m=s',
#			      'another_argument|o=s',
#			      'optional_argument|s=s',
#			      'optional_argument2|f=s',
			      'log|l=s',
			      'help|h') || pod2usage();

    ## display documentation
    if( $options{'help'} ){
	pod2usage( {-exitval => 0, -verbose => 2, -output => \*STDERR} );
    }

    ## make sure everything passed was peachy
    &check_parameters(\%options);

    return %options;
}

sub check_parameters {
    my $options = shift;
    
    ## make sure required arguments were passed
    my @required = qw( conf );
    for my $option ( @required ) {
        unless  ( defined $options->{$option} ) {
            die "--$option is a required option";
        }
    }
    
    ##
    ## you can do other things here, such as checking that files exist, etc.
    ##
    
    unless ( -e $options->{conf} ) {
	die "Unable to read --conf $options->{conf}"
    }

    ## handle some defaults
#    $options->{optional_argument2} = 'foo'  unless ($options->{optional_argument2});
}
