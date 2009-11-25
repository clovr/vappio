#!/usr/bin/perl

=head1 NAME

add_instance.pl - Adds instance to a cluster using the credentials and cloud specified in --conf.  

=head1 SYNOPSIS

USAGE: add_instance.pl 
            --master=hostname
            --user_data=./exec_user-data.tmpl
            --nodes=10
            --instance_type=m1.large
            --conf=/path/to/config 


=head1 OPTIONS

=head1  DESCRIPTION


=head1  INPUT

=head1  OUTPUT

=head1  CONTACT

=cut

use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);
use Pod::Usage;

use Config::IniFiles;
use HTML::Template;

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

# overwrite config values with anything the use passed in
# todo

# confirm required values
foreach my $req ( qw( EC2_HOME EC2_URL EC2_JVM_ARGS EC2_PRIVATE_KEY EC2_CERT JAVA_HOME IMAGE KEY GROUP MASTER_INSTANCE_TYPE MASTER_USER-DATA_TMPL EXEC_USER-DATA_TMPL EXEC_NODES ) ) {
#    die "Missing required parameter $req" unless $cfg->exists('general', $req); #doesn't work?
    die "Missing required parameter $req" unless defined($cfg->val('general', $req));
}

# export some variables
foreach (qw( EC2_HOME EC2_URL EC2_JVM_ARGS JAVA_HOME EC2_PRIVATE_KEY EC2_CERT )) {
    $ENV{$_} = $cfg->val('general', $_);
}

print "$ENV{EC2_JVM_ARGS}\n";

# Confirm that these files exist
foreach ( qw( MASTER_USER-DATA_TMPL EXEC_USER-DATA_TMPL CLUSTER_PRIVATE_KEY ) ) {
    (-e $cfg->val('general', $_) ) || die "File $_ ". $cfg->val('general', $_) ." does not exist";
    (-r $cfg->val('general', $_) ) || die "File $_ not readable";
}

my $RUN = $cfg->val('general', 'EC2_HOME')."/bin/ec2-run-instances";
my $DESCRIBE = $cfg->val('general', 'EC2_HOME')."/bin/ec2-describe-instances";

# parse security groups
my @groups = split(",", $cfg->val('general', "GROUP"));
my $key = $cfg->val('general', 'KEY');
my $image = $cfg->val('general', 'IMAGE');

my $instance_type = $opts{instance_type} || 'm1.small';
my $nodes = $opts{nodes} || 1;

# Settings for launch script
my $cmd = "cat ".$cfg->val('general', 'CLUSTER_PRIVATE_KEY');
my $CLUSTER_PRIVATE_KEY = qx($cmd);
die "Problem with cluster private key" unless defined($CLUSTER_PRIVATE_KEY);

# This will be appended to authorized_keys
$cmd = "ssh-keygen -y -f ".$cfg->val('general', 'CLUSTER_PRIVATE_KEY');
my $CLUSTER_PUBLIC_KEY = qx($cmd);
die "Problem with cluster public key" unless defined($CLUSTER_PUBLIC_KEY);

my @ec2_describe_info = qx( $DESCRIBE );
my $exit_value = $? >> 8;
die "Unable to ec2-describe-instances" if $exit_value;

my $found_instance = 0;
my ($state, $public_dns, $private_dns);
foreach ( @ec2_describe_info ) {
    next unless $_ =~ /^INSTANCE/;
    my %instance = parse_instance($_);
    next unless ($instance{public_dns} eq $opts{master});
    ++$found_instance;
    ($state, $public_dns, $private_dns) = @instance{ qw(state public_dns private_dns) };
    print "$state $public_dns $private_dns\n";
}

if(!defined $state)
{
    die "Can't find master hostname $opts{master} running $DESCRIBE";
}

_log( "MASTER $opts{master} $public_dns\t$private_dns");

# Customize launch script
my $templ = HTML::Template->new( filename => $opts{user_data} );
if ( $cfg->val('general', 'CLOUD_TYPE') eq 'NIMBUS' ) {
    $templ->param(MASTER_PRIVATE_DNS => $public_dns);
}
else {
    $templ->param(MASTER_PRIVATE_DNS => $private_dns);
}
$templ->param(CLUSTER_PRIVATE_KEY => $CLUSTER_PRIVATE_KEY);
$templ->param(CLUSTER_PUBLIC_KEY => $CLUSTER_PUBLIC_KEY);

my $sh = $cfg->val('general', 'SECURE_TEMP')."/user-data.sh" ;
open (my $EOUT, ">$sh")  || die "Unable to write SECURE_TEMP $sh:$!";
$templ->output(print_to => *$EOUT);
close($EOUT);

# Launch the Nodes
$cmd = "$RUN -k $key -t $opts{instance_type} -f $sh -n $nodes";
foreach (@groups) {
    $cmd .= " -g $_";
}
$cmd .= " $image";
_log("$cmd");


print "$cmd\n";
my @ec2_run_info = qx($cmd);
$exit_value = $? >> 8;
die "Unable to launch nodes" if $exit_value;

_log( "Launched nodes:\n".join("\n", @ec2_run_info) );

print "View the control panel in your web browser: http://$public_dns/ergatis\n";


exit(0);

#
# SUBROUTINES
#

sub parse_instance {
    my $line = shift;
    chomp($line);
    my @row = split("\t", $line);
    shift(@row); # get rid of INSTANCE

    # store as hash using a hash slice
    my %instance;
    @instance{ qw(instance_id ami public_dns private_dns state key index type launch zone monitor  ) } = @row;
    return %instance;
}

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
			      'master|m=s',
			      'nodes|n=s',
			      'user_data|t=s',
			      'instance_type|i=s',
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
