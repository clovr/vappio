#!/usr/bin/perl

=head1 NAME

run_prok_pipeline.pl - Will start a cluster, upload necessary files, run a pipeline, monitor the pipeline.

=head1 SYNOPSIS

 USAGE: run_prok_pipeline.pl
       --prok_conf=/path/to/file.conf
       --help

=head1 OPTIONS

B<--prok_conf_file,-p>
    Used to specify all the options for a prok run

B<--help,-h>
    Print this message

=head1  DESCRIPTION

    Script will bring up cluster using vappio-py command line scripts (must have envvar $VAPPIO_HOME set)
    and upload necessary files (i.e. input sff file and reference dbs).  It will then run the pipeline and spit out
    statistics about the run. After the pipeline has finished, will download the correct set of files for use.

    The input section of this perldoc will describe the options for the prok_conf file.  The clovr conf file should
    be described by the clovr package.
 
=head1  INPUT
    
=head1 OUTPUT

    

=head1  CONTACT

    Kevin Galens
    kevingalens@gmail.com

=cut

use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);
use Pod::Usage;
use Config::IniFiles;
$|++;

my %options;
my $results = GetOptions (\%options,
                          'prok_conf|p=s',
                          'help|h'
                          ) || &_pod;

my $config;
my $lfh; # Log File Handle
my $debug_level = 1; #Debug level
my ($DEBUG, $WARN, $ERROR) = (3,2,1);
my $vappio_cli;

&init(\%options);

# Check to see if the cluster is running, if not, start one.
# If the number of exec nodes currently up and running is less then
# those in the config file, will add more.
&check_cluster( $config );

# Upload the necessary files. Check to see if they are already there first and
# don't upload if present. Uses default tags. If data is already present under an
# unexpected tag, the script will reupload the files.
#&upload_files( $config );

#Wait for the uploads to finish. does_remote_tag_exist should return 1 for both
#the input file and the ref db
&_log($DEBUG, "\n");
while( !(&does_remote_tag_exist( $config, $config->val('input', 'input_tag') ) &&
       &does_remote_tag_exist( $config, $config->val('input', 'reference_tag') ) ) ) {
    &_log($DEBUG, "\rWaiting for files to upload", 1);
    foreach my $i ( 1..10 ) {
        &_log($DEBUG, ".",1);
        sleep(1);
    }
    &_log($DEBUG, "                                                 ",1);
}

&_log($DEBUG, "\nBoth input and ref db have finished copying");

#And now run the pipeline (since we have all of the necessary files uploaded)
my $continue = &check_pipeline( $config );

if( $continue ) {
    &download_data( $config );
}


sub check_cluster {
    my ($cfg) = @_;
    my $cluster_tag = $cfg->val('cluster', 'cluster_tag')
        or &_config_error( 'cluster', 'cluster_tag' );
    &_log($DEBUG, "Searching for cluster $cluster_tag");

    #host that the Web Service is running on
    my $host = $cfg->val('cluster', 'host')
        or &_config_error( 'cluster', 'host' );
    
    my $clusterInfo_exec = $vappio_cli."/clusterInfo.py";
    my $cmd = $clusterInfo_exec." --name $cluster_tag ";
    $cmd .= "--host $host " unless( $host eq 'local' );
    $cmd .= "2>&1";
    &_log($DEBUG, "Running [$cmd]");


    my $master_ip;
    my $num_exec_nodes;

    #Capture the output
    open( CMD, "$cmd |" ) or &_log($ERROR, "Couldn't execute command $cmd ($!)");
    while( my $line = <CMD> ) {
        chomp($line);
        if( $line =~ /Master IP\: (.*)/ ) {
            $master_ip = $1;
        } elsif( $line =~ /(\d+) exec nodes/ ) {
            $num_exec_nodes = $1;
        }
    }
    close(CMD);

    if( $master_ip ) {
        my $key = $cfg->val('cluster', 'key') 
            or &_config_error('cluster', 'key');
        my $ssh_cmd = "ssh -i $key root\@$master_ip";
        &_log($DEBUG, "Cluster is running\nMaster IP: $master_ip\nExec Nodes: $num_exec_nodes\nSSH: $ssh_cmd");
        
        $cfg->newval('cluster', 'master_ip', $master_ip );
        $cfg->newval('cluster', 'ssh', $ssh_cmd);

        my $config_exec_nodes = $cfg->val('cluster', 'exec_nodes');
        $cfg->setval('cluster', 'exec_nodes', $num_exec_nodes );
        if( $config_exec_nodes > $num_exec_nodes ) {
            &_log($DEBUG, "Would have added instances, but clusterInfo script doesn't properly return the number ".
                  "of exec nodes. So I can't believe it.");
            #&add_instances( $cfg, $config_exec_nodes );
        }

    } else {
        &_log($DEBUG, "Cluster is not running. Will start it up");
        &start_cluster( $cfg );
    }
}

sub add_instances {
    my ($cfg, $total_exec) = @_;

    my $cluster_tag = $cfg->val('cluster', 'cluster_tag')
        or &_config_error( 'cluster', 'cluster_tag' );
    my $current_exec = $cfg->val('cluster', 'exec_nodes')
        or &_config_error( 'cluster', 'exec_nodes' ); 
    my $delta_exec_nodes = $total_exec - $current_exec;
    if( $delta_exec_nodes <= 0 ) {
        &_log($WARN, "Cannot add $delta_exec_nodes");
    } else {
        my $addInstances_exec = $vappio_cli."/addInstances.py";
        my $cmd = $addInstances_exec." --name $cluster_tag --num $delta_exec_nodes";
        my $exit_val = system( $cmd );
        if( $exit_val != 0 ) {
            &_log($WARN, "WARN: Could not add instances to cluster. Continuing with $current_exec exec nodes");
        } else {
            $cfg->setval('cluster', 'exec_nodes', $total_exec);
        }
        &_log($DEBUG, "Just added $delta_exec_nodes to cluster. They will come online shortly");
    }
}

sub start_cluster {
    my ($cfg) = @_;

    my $cluster_tag  = $cfg->val('cluster', 'cluster_tag')
        or &_config_error( 'cluster', 'cluster_tag' );
    my $clovr_conf = $cfg->val('cluster', 'clovr_conf' )
        or &_config_error( 'cluster', 'clovr_conf' );
    my $exec_nodes = $cfg->val( 'cluster', 'exec_nodes' )
        or &_config_error( 'cluster', 'exec_nodes' );
    my $host = $cfg->val('cluster', 'host')
        or &_config_error( 'cluster', 'host' );
    
    
    my $startCluster_exec = $vappio_cli."/startCluster.py";
    my $cmd = $startCluster_exec." --conf $clovr_conf --name $cluster_tag --num $exec_nodes --ctype ec2 -b";
    $cmd .= " --host $host" unless( $host eq 'local' );
    &_log($DEBUG, "Starting cluster with command $cmd");
    my $exit_val = system($cmd);
    if( $exit_val != 0 ) {
        &_log($ERROR, "Had issues starting up cluster with cmd $cmd\nReturn value of ".($exit_val >> 8));
    }
}

sub upload_files {
    my ($cfg) = @_;

    my $input_sff_file = $cfg->val('input', 'input_sff_file') or
            &_config_error( 'input', 'input_sff_file');
    
    my $input_tag = $cfg->val('input', 'input_tag') or 
        &_config_error( 'input', 'input_tag' );
    my $ref_tag = $cfg->val('input', 'reference_tag') or
        &_config_error( 'input', 'reference_tag' );

    #Deal with input
    my $wait = 0;
    my ($retval, @files) = &does_remote_tag_exist( $cfg, $input_tag );
    if( !$retval ) {
        &_log($DEBUG, "The tag, $input_tag, did not exist, so tagging/uploading it");
        &tag_data( $cfg, $input_tag, $input_sff_file );
        &run_upload_cmd( $cfg, $input_tag );
    } elsif( @files == 0 ) {
        $wait = 1;
    }

    #deal with ref_db
    ($retval, @files) = &does_remote_tag_exist( $cfg, $ref_tag );
    if( $retval != 0 ) {
        &_log($DEBUG, "The reftag $ref_tag doesn't exist, so uploading");
        &run_upload_cmd( $cfg, $ref_tag );
    } elsif( @files == 0 ) {
        $wait = 1;
    }

    return $wait;
}

sub tag_data {
    my ($cfg, $tag, $file) = @_;
    
    my $host = $cfg->val('cluster', 'host')
        or &_config_error( 'cluster', 'host' );

    #First we should tag the files on the local VM
    my $tagData_exe = $vappio_cli."/tagData.py";
    my $cmd = $tagData_exe." --name local --tag-name $tag ";
    $cmd .= "--host $host " unless( $host eq 'local' );
    $cmd .= "-o -r $file";
    &_log($DEBUG, "Running command $cmd");
    my $ev = system($cmd);
    if( $ev != 0 ) {
        &_log($ERROR, "Error running $cmd. Exit value: ".($? >> 8 ) );
    }
    return 1;
}

sub run_upload_cmd {
    my ($cfg, $tag) = @_;

    my $cluster_name = $cfg->val('cluster', 'cluster_tag');
    my $host = $cfg->val('cluster', 'host') or
        &_config_error('cluster', 'host');

    #Now run upload command
    my $uploadFiles_exe = $vappio_cli."/uploadTag.py";
    my $cmd = $uploadFiles_exe." --tag-name $tag --dst-cluster $cluster_name --expand";
    $cmd .= " --host $host" unless( $host eq 'local' );
    &_log($DEBUG, "Running cmd: $cmd");
    my $exit_val = system( $cmd );
    if( $exit_val != 0 ) {
        &_log($ERROR, "Problem runing cmd $cmd. Check /tmp/uploadTag.log for output. Exited with status: ".($exit_val >> 8));
    }
}

sub does_remote_tag_exist {
    my ($cfg, $input_tag) = @_;
    
    my $cluster_name = $cfg->val('cluster', 'cluster_tag');
    my $host = $cfg->val('cluster', 'host') or
        &_config_error('cluster', 'host');

    my $cmd = $vappio_cli."/queryTag.py --name $cluster_name --tag-name $input_tag";
    $cmd .= " --host $host" unless( $host eq 'local' );
    $cmd .= " 2>&1";
    my @files = ();
    #&_log($DEBUG, "Checking for remote tag with command: [$cmd]");
    open(CMD, "$cmd |") or die("Could not run command $cmd ($!)");
    chomp( @files = <CMD> );
    close(CMD);

    my $retval = 0;
    if( $? == 0 && @files != 0 ) {
        $retval = 1;
    }

    return ($retval);
}

sub check_pipeline {
    my ($cfg) = @_;
    my $runPipeline_exec = $vappio_cli."/runPipeline.py";
    my $pipeline_name = $cfg->val('input', 'pipeline_name') or
        &_config_error( 'input', 'pipeline_name' );
    my $cluster_tag = $cfg->val('cluster', 'cluster_tag') or
        &_config_error( 'cluster', 'cluster_tag' );
    
    #does the pipeline exist and what is its state?
    my $state;
    if( $state = &does_pipeline_exist( $cfg, $cluster_tag, $pipeline_name ) ) {
        &_log($DEBUG, "Pipeline $pipeline_name is in $state state");
    } else {
        &start_pipeline( $cfg );
    }
    
    my $master_ip = $cfg->val('cluster', 'master_ip' )
        or &_config_error( 'cluster', 'master_ip' );
    &_log($DEBUG, "Monitor the pipeline from this address: http://$master_ip/ergatis");
    &_log($DEBUG, "Run this script again with the same config file when the pipeline is complete to download the data");
    my $continue = 0;
    if( $state eq 'complete' ) {
        $continue = 1;
    }
    return $continue;
}

sub start_pipeline {
    my ($cfg) = @_;

    #Get all the needed variables
    my $trim = $cfg->val('input', 'trim' );
    my $clear = $cfg->val('input', 'clear' );
    my $spec_file = $cfg->val('input', 'spec_file');
    my $pipeline_name = $cfg->val('input', 'pipeline_name' ) or
        &_config_error( 'input', 'pipeline_name' );
    my $output_prefix = $cfg->val('input', 'output_prefix' ) or
        &_config_error( 'input', 'output_prefix' );
    my $organism = $cfg->val('input', 'organism' ) or
        &_config_error('input', 'organism' );
    my $input_tag = $cfg->val('input', 'input_tag') or
        &_config_error('input', 'input_tag');
    my $reference_tag = $cfg->val('input', 'reference_tag') or
        &_config_error('input', 'reference_tag');
    my $cluster_tag = $cfg->val('cluster', 'cluster_tag' ) or
        &_config_error( 'cluster', 'cluater_tag' );
    my $exec_nodes = $cfg->val('cluster', 'exec_nodes') or
        &_config_error('cluster', 'exec_nodes');
    my $clovr_conf = $cfg->val('cluster', 'clovr_conf') or
        &_config_error('cluster', 'clovr_conf');
    
    #Create a new log
    my $log = "/tmp/runPipeline.$$.log";

    #The executable
    my $runPipeline_exec = $vappio_cli."/runPipeline.py";

    #build the command
    my $cmd = $runPipeline_exec." --name $cluster_tag --pipeline_name $pipeline_name --pipeline barebones_prok ".
        "-- --INPUT_FILE_LIST $input_tag --OUTPUT_PREFIX $output_prefix --ORGANISM $organism --GROUP_COUNT ".
        ($exec_nodes * 2)." --DATABASE_PATH $reference_tag --conf $clovr_conf";
    $cmd .= " --TRIM $trim" if( $trim );
    $cmd .= " --CLEAR $clear" if( $clear );
    $cmd .= " --SPEC_FILE $spec_file" if( $spec_file );
    $cmd .= " 2>&1 > $log";

    &_log($DEBUG, "Starting runPipeline: [$cmd]");

    #and set it running
    my $pipeline_id;
    open( RUN, "$cmd |") or &_log($ERROR, "Could not run command $cmd: ($!)");
    while( my $line = <RUN> ) {
        if( $line =~ /Pipeline Id\:\s+(\d+)/ ) {
            $pipeline_id = $1;
            last;
        }
    }
    close(RUN);

    unless( $pipeline_id ) {
        &_log($ERROR, "Something went wrong running runPipeline.pl\nCheck $log for stderr and stdout.\nCOMMAND: $cmd");
    }
}

sub does_pipeline_exist {
    my ($cfg, $cluster_tag, $pipeline_name) = @_;
    my $retval = 0;

    my $pipelineStatus_exec = $vappio_cli."/pipelineStatus.py";
    my $cmd = $pipelineStatus_exec." --name $cluster_tag $pipeline_name";
    &_log($DEBUG, "Checking for status of pipeline $pipeline_name on cluster $cluster_tag");
    open(CMD, "$cmd |") or die("Could not run command $cmd ($!)");
    while(my $line = <CMD>) {
        chomp( $line );
        if( $line =~ /$pipeline_name\s+(.*)/ ) {
            $retval = (split(/\s+/, $1))[0];
        }
    }
    close(CMD);
    return $retval;
}

sub download_data {
    my ($config) = @_;
    my $output_dir = $config->val('output', 'output_directory')
        or &_config_error("output", "output_directory");
    my $cluster_tag = $config->val('cluster', 'cluster_tag');
    my $pipeline_name = $config->val('input', 'pipeline_name');
    
    system("mkdir $output_dir") unless( -d $output_dir );
    
    my $downloadPipelineOutput_exe = $vappio_cli."/downloadPipelineOutput.py";
    my $cmd = $downloadPipelineOutput_exe." --name $cluster_tag --pipeline $pipeline_name ".
        "--output_dir $output_dir --overwrite";
    &_log($DEBUG, "Downloading pipeline data. This could take a while. [$cmd]");
    system("$cmd");
    if( $? != 0 ) {
        &_log($ERROR, "Failed downloading pipeline. Something went wrong (error code: ".($? >> 8));
    }
    &_log($DEBUG, "Check dir [$output_dir] for pipeline output");
}

sub init {
   my $opts = shift;

   #if they want help, print the perldoc
   if( $opts->{'help'} ) {
       &_pod;
   }

   # check for the only required option
   if( $opts->{'prok_conf'} ) {
       $config = &parse_config( $opts->{'prok_conf'} );
   } else {
       die("Option prok_conf is required");
   }

   # setup the logging
   my $logfile;
   if( $logfile = $config->val('output', 'log_file') ) {
       open( $lfh, "> $logfile" ) or die("Can't open log file [$logfile] for writing ($!)");
   } else {
       $logfile = "/tmp/$0.log";
       open( $lfh, "> $logfile") or die("Can't open default log file [/tmp/$0.log] for writing ($!)");
   }
   $debug_level = $config->val('output', 'debug_level') if( $config->val('output', 'debug_level') );
   &_log($DEBUG, "Setup logging to $logfile with debug level $debug_level");
   &_log($DEBUG, "Starting $0 at ".localtime );

   #the VAPPIO_HOME env var must be set
   if( !exists( $ENV{'VAPPIO_HOME'} ) ) {
       &_log($ERROR, "The environment variable \$VAPPIO_HOME is not set. Please point to a local copy of the vappio checkout");
   }

   $vappio_cli = $ENV{'VAPPIO_HOME'}."/vappio-py/vappio/cli";
   &_log($DEBUG, "Using vappio cli scripts in dir $vappio_cli");

}

sub parse_config {
    my ($file) = @_;
    return new Config::IniFiles( -file => $file );
}

sub _config_error {
    my ($section, $param) = @_;
    &_log($ERROR, "Could not find config variable $param in section $section in config file");
}

sub _log {
    my ($level, $msg, $no_newline) = @_;
    if( $level == $ERROR ) {
        print $lfh $msg;
        print "\n" unless( $no_newline );
        die($msg);
    }
    if( $level <= $debug_level ) {
        print $msg;
        print "\n" unless( $no_newline );
        print $lfh $msg;
        print "\n" unless( $no_newline );
    }
}

sub _pod {
    pod2usage( {-exitval => 0, -verbose => 2, -output => \*STDERR} );
}
