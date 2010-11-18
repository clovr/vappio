#!/usr/bin/env perl

use lib ( @INC, '/opt/ergatis/lib/perl5');
use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);
use Ergatis::SavedPipeline;
use Ergatis::ConfigFile;

my $repoRoot = "/mnt/projects/clovr";
my $ergatisConfigFile = "/var/www/ergatis/cgi/ergatis.ini";

my %options;
my $results = GetOptions (\%options, 
			  'pipeline_id=s',
			  'taskname=s',
			  'queue=s'
                          );

my $pipeline_id = $options{'pipeline_id'} if( $options{'pipeline_id'} );
my $taskName = $options{'taskname'} if( $options{'taskname'} );
my $queue = $options{'queue'} if ( $options{'queue'} );

die("Must specify a pipeline_id") unless($pipeline_id);
die("Must specify a taskname") unless($taskName);

$queue = 'pipelinewrapper.q' unless($queue);

my $pipeline_id = &make_pipeline($repoRoot, $pipeline_id, $taskName, $queue);

##
# Pring the pipeline
print "$pipeline_id\n";

sub make_pipeline {
    my ($repository_root, $pipeline_id, $taskName, $queue) = @_;

    my $pipeline = new Ergatis::Pipeline( id   => $pipeline_id,
                                          path => "$repository_root/workflow/runtime/pipeline/$pipeline_id/pipeline.xml"
                                          );

    my $ergatisConfig = new Ergatis::ConfigFile(-file => $ergatisConfigFile);
    $ergatisConfig->newval('workflow_settings', 'observer_scripts', "ergatisObserver.py:setlife:$taskName");
    $ergatisConfig->newval('workflow_settings', 'submit_pipelines_as_jobs', '1');
    $ergatisConfig->newval('workflow_settings', 'pipeline_submission_queue', $queue);
    $pipeline->run('ergatis_cfg' => $ergatisConfig);
    return $pipeline_id
}

