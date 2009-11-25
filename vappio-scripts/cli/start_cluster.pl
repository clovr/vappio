#!/usr/bin/perl

=head1 NAME

start_cluster.pl - Starts a new cluster using the credentials and cloud specified in --conf.  Returns the IP address of the master node for the cluster.  This master node is then ready to accept requests

=head1 SYNOPSIS

USAGE: start_cluster.pl 
            --conf=/path/to/config 
            --another_argument=/path/to/somedir
          [ --optional_argument=/path/to/somefile.list 
            --optional_argument2=1000
	    --log=log.out
   	    --help
          ]

=head1 OPTIONS

B<--some_argument,-i>
    here you'll put a longer description of this argument that can span multiple lines. in 
    this example, the script has a long option and a short '-i' alternative usage.

B<--another_argument,-o>
    here's another named required argument.  please try to make your argument names all
    lower-case with underscores separating multi-word arguments.

B<--optional_argument,-s>
    optional.  you should preface any long description of optional arguments with the
    optional word as I did in this description.  you shouldn't use 'optional' in the
    actual argument name like I did in this example, it was just to indicate that
    optional arguments in the SYNOPSIS should go between the [ ] symbols.

B<--optional_argument2,-f>
    optional.  if your optional argument has a default value, you should indicate it
    somewhere in this description.   ( default = foo )

B<--log,-l> 
    Log file

B<--help,-h>
    This help message

=head1  DESCRIPTION

put a longer overview of your script here.

=head1  INPUT

the input expectations of your script should be here.  pasting in examples of file format
expected is encouraged.

=head1  OUTPUT

the output format of your script should be here.  if your script manipulates a database,
you should document which tables and columns are affected.

=head1  CONTACT

    Aaron Gussman
    agussman@som.umaryland.edu

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

my $master_instance_type = $cfg->val('general', 'MASTER_INSTANCE_TYPE');
my $exec_instance_type = $cfg->val('general', 'EXEC_INSTANCE_TYPE');
my $exec_nodes = $cfg->val('general', 'EXEC_NODES');


# Settings for launch script
my $cmd = "cat ".$cfg->val('general', 'CLUSTER_PRIVATE_KEY');
my $CLUSTER_PRIVATE_KEY = qx($cmd);
die "Problem with cluster private key" unless defined($CLUSTER_PRIVATE_KEY);

# This will be appended to authorized_keys
$cmd = "ssh-keygen -y -f ".$cfg->val('general', 'CLUSTER_PRIVATE_KEY');
my $CLUSTER_PUBLIC_KEY = qx($cmd);
die "Problem with cluster public key" unless defined($CLUSTER_PUBLIC_KEY);

# Customize master launch script
my $template = HTML::Template->new( filename => $cfg->val('general', 'MASTER_USER-DATA_TMPL') );
$template->param(CLUSTER_PRIVATE_KEY => $CLUSTER_PRIVATE_KEY);
$template->param(CLUSTER_PUBLIC_KEY => $CLUSTER_PUBLIC_KEY);

my $master_sh = $cfg->val('general', 'SECURE_TEMP')."/master_user-data.sh" ;
open (my $MOUT, ">$master_sh")  || die "Unable to write SECURE_TEMP $master_sh:$!";
$template->output(print_to => *$MOUT);
close($MOUT);

# Launch the Master Node
my $launch_cmd = "$RUN -k $key -t $master_instance_type -f $master_sh";
foreach (@groups) {
    $launch_cmd .= " -g $_";
}
$launch_cmd .= " $image";
_log( "$launch_cmd");

my @ec2_run_info = qx($launch_cmd);
my $exit_value = $? >> 8;
die "Unable to launch master" if $exit_value;

my %launch_instance = parse_instance( $ec2_run_info[1] );

_log( $launch_instance{instance_id});

my ($master_instance_id, $state, $public_dns, $private_dns) = @launch_instance{ qw( instance_id state public_dns private_dns ) };

# monitor until the instance comes online
while ( $state eq 'pending' ) {
    sleep(10);
    print "Querying for status of $master_instance_id... ";

    my @ec2_describe_info = qx( $DESCRIBE );
    $exit_value = $? >> 8;
    die "Unable to ec2-describe-instances" if $exit_value;

    my $found_instance = 0;
    foreach ( @ec2_describe_info ) {
	next unless $_ =~ /^INSTANCE/;
	my %instance = parse_instance($_);
	next unless ($instance{instance_id} eq $master_instance_id);
	++$found_instance;
	($state, $public_dns, $private_dns) = @instance{ qw(state public_dns private_dns) };
	print "$state\n";
    }

    die "Unable to locate instance id $master_instance_id in ec2-describe-instances output" unless ($found_instance);
}

if ($state ne 'running') {
    die "Problem with launching Master, state $state != 'running'";
}


_log( "$master_instance_id\t$public_dns\t$private_dns");


# Customize exec launch script
my $exec_templ = HTML::Template->new( filename => $cfg->val('general', 'EXEC_USER-DATA_TMPL') );
if ( $cfg->val('general', 'CLOUD_TYPE') eq 'NIMBUS' ) {
    $exec_templ->param(MASTER_PRIVATE_DNS => $public_dns);
}
else {
    $exec_templ->param(MASTER_PRIVATE_DNS => $private_dns);
}
$exec_templ->param(CLUSTER_PRIVATE_KEY => $CLUSTER_PRIVATE_KEY);
$exec_templ->param(CLUSTER_PUBLIC_KEY => $CLUSTER_PUBLIC_KEY);

my $exec_sh = $cfg->val('general', 'SECURE_TEMP')."/exec_user-data.sh" ;
open (my $EOUT, ">$exec_sh")  || die "Unable to write SECURE_TEMP $exec_sh:$!";
$exec_templ->output(print_to => *$EOUT);
close($EOUT);

# Launch the Exec Nodes
my $exec_cmd = "$RUN -k $key -t $exec_instance_type -f $exec_sh -n $exec_nodes";
foreach (@groups) {
    $exec_cmd .= " -g $_";
}
$exec_cmd .= " $image";
_log("$exec_cmd");

@ec2_run_info = qx($exec_cmd);
$exit_value = $? >> 8;
die "Unable to launch exec nodes" if $exit_value;

_log( "Launched exec nodes:\n".join("\n", @ec2_run_info) );

print "View the control panel in your web browser: http://$public_dns/ergatis\n";
print "CloVR instance id: $master_instance_id\n";

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
