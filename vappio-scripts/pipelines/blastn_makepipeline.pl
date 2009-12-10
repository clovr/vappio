#!/bin/env perl

use lib ( @INC, '/opt/ergatis/lib/perl5');
use strict;
use warnings;
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);
use Ergatis::SavedPipeline;


my $templateFile = "/mnt/projects/clovr/workflow/project_saved_templates/blastn_tmpl/pipeline.layout";
my $repoRoot = "/mnt/projects/clovr";
my $idRepo = "/opt/ergatis/global_id_repository";

my %options;
my $results = GetOptions (\%options, 
			  'config=s'
                          );

my $configFile = $options{'config'} if( $options{'config'} );

die("Must specify a config file") unless($configFile);

my $pipeline_id = &make_pipeline($templateFile, $repoRoot, $idRepo, $configFile);


sub make_pipeline {
    my ($pipeline_layout, $repository_root, $id_repo, $config) = @_;
    my $template = new Ergatis::SavedPipeline( 'template' => $pipeline_layout );
    $template->configure_saved_pipeline( $config, $repository_root, $id_repo );
    return $template->pipeline_id();           
}

