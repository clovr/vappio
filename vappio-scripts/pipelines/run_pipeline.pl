#!/usr/bin/env perl

use lib ( @INC, '/opt/ergatis/lib/perl5');
use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);
use Ergatis::SavedPipeline;
use Ergatis::ConfigFile;

#my $templateLayout = "/mnt/projects/clovr/workflow/project_saved_templates/blastn_tmpl/pipeline.layout";
my $repoRoot = "/mnt/projects/clovr";
my $idRepo = "/opt/ergatis/global_id_repository";
my $ergatisConfigFile = "/var/www/ergatis/cgi/ergatis.ini";

my %options;
my $results = GetOptions (\%options, 
			  'config=s',
			  'templatelayout=s',
			  'taskname=s'
                          );

my $configFile = $options{'config'} if( $options{'config'} );
my $templateLayout = $options{'templatelayout'} if( $options{'templatelayout'} );
my $taskName = $options{'taskname'} if( $options{'taskname'} );

die("Must specify a config file") unless($configFile);
die("Must specify a template") unless($templateLayout);
die("Must specify a taskname") unless($taskName);

my $pipeline_id = &make_pipeline($templateLayout, $repoRoot, $idRepo, $configFile);

##
# Pring the pipeline
print "$pipeline_id\n";

sub make_pipeline {
    my ($pipeline_layout, $repository_root, $id_repo, $config) = @_;
    my $template = new Ergatis::SavedPipeline( 'template' => $pipeline_layout );
    $template->configure_saved_pipeline( $config, $repository_root, $id_repo );
    my $pipeline_id = $template->pipeline_id();

    my $pipeline = new Ergatis::Pipeline( id   => $pipeline_id,
                                          path => "$repository_root/workflow/runtime/pipeline/$pipeline_id/pipeline.xml"
                                          );

    my $ergatisConfig = new Ergatis::ConfigFile(-file => $ergatisConfigFile);
    $ergatisConfig->newval('workflow_settings', 'observer_scripts', 'ergatisObserver.py:setlife:$taskName');
    $pipeline->run('ergatis_cfg' => $ergatisConfig);
    return $pipeline_id
}

