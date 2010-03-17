package Vappio;

use strict;
use warnings;
use JSON;
use HTTP::Request::Common qw(POST);
use LWP::UserAgent;
use Data::Dumper;

sub new {
    my ($class, $url) = @_;
    my $self = {};
    bless( $self, $class );
    
    #setup a UserAgent for requests
    $self->ua( new LWP::UserAgent );

    #the only option required is the base URL
    if( defined( $url ) ) {
        my $res = $self->ua->get( $url );
        die("Invalid url: $url") if( !$res->is_success );
        $self->url( $url );
    } else {
        die("Parameter url is missing from constructor");
    }

    return $self;
}

############# CLUSTER ROUTINES ##################
sub clusterInfo {
    my ($self, $cluster_name) = @_;
    &_parameter_error( "cluster_name", "clusterInfo" ) unless( $cluster_name );

    my $resource = "/vappio/clusterInfo_ws.py";
    return $self->_make_request( $resource, { 'name' => $cluster_name } );
}
sub listClusters {
    my ($self) = @_;
    my $resource = "/vappio/listClusters_ws.py";
    return @{$self->_make_request( $resource, {} )};
}
sub addInstances {
    my ($self, $cluster_name, $num, %options) = @_;
    &_parameter_error( "cluster_name", "clusterInfo" ) unless( $cluster_name );
    &_parameter_error( "num", "clusterInfo" ) unless( $num );

    my $resource = "/vappio/addInstances_ws.py";
    my $req_opts = { 'name' => $cluster_name, 'num' => $num };
    $req_opts->{'update_dirs'} = $options{'update_dirs'} if( $options{'update_dirs'} );
    return $self->_make_request( $resource, $req_opts );
}
sub runCommandOnCluster {
    my( $self, $cluster_name, $cmd ) = @_;
    
    die("runCommandOnCluster subroutine not implemented yet");

    &_parameter_error( "cluster_name", "clusterInfo" ) unless( $cluster_name );
    &_parameter_error( "cmd", "clusterInfo" ) unless( $cmd );
    
    my $resource = "/vappio/runCommandOnCluster_ws.py";
}
sub startCluster {
    my ($self, $cluster_name, $conf, $num, $ctype, %options) = @_;
    &_parameter_error( "cluster_name", "clusterInfo" ) unless( $cluster_name );
    &_parameter_error( "conf", "clusterInfo" ) unless( $conf );
    &_parameter_error( "ctype", "clusterInfo" ) unless( $ctype );
    &_parameter_error( "num", "clusterInfo" ) unless( $num );

    my $resource = "/vappio/startCluster_ws.py";

    my $req_opts = {'name' => $cluster_name, 'conf' => $conf,
                    'ctype' => $ctype, 'num' => $num };
    $req_opts->{'update_dirs'} = $options{'update_dirs'} if( $options{'update_dirs'} );
    return $self->_make_request( $resource, $req_opts );
}
sub terminateCluster {
    my ($self, $cluster_name) = @_;
    &_parameter_error( 'name', 'terminateCluster' ) unless( $cluster_name );
    my $resource = "/vappio/terminateCluster_ws.py";
    return $self->_make_request( $resource, { 'name' => $cluster_name } );
}

#################### TAGGING/FILES ####################
sub queryTag {
    my ($self, $cluster_name, $tag_name) = @_;
    &_parameter_error("cluster_name", "queryTag") unless( $cluster_name );
    &_parameter_error("tag_name", "queryTag" ) unless( $tag_name );

    my $resource = "/vappio/queryTag_ws.py";
    return $self->_make_request( $resource, 
                                 { 'name' => $cluster_name,
                                   'tag_name' => $tag_name } );

}
sub tagData {
    my ($self, $tag_name, $path, %opts) = @_;
    &_parameter_error("tag_name", "tagData") unless( $tag_name );
    &_parameter_error("path", "tagData" ) unless( $path );
    
    my $options = { 'tag_name' => $tag_name, 'files' => $path };
    foreach my $param ( qw(recursive expand append overwrite tag_base_dir name) ) {
        if( $opts{$param} ) {
            $options->{$param} = $opts{$param};
        } else {
            $options->{$param} = "";
        }
    }
    $options->{'name'} = 'local' unless( $opts{'name'} );
    
    my $resource = "/vappio/tagData_ws.py";
    return $self->_make_request( $resource, $options );
}
sub uploadTag {
    my ($self, $tag_name, $dst_cluster, %options) = @_;
    &_parameter_error("tag_name", "tagData") unless( $tag_name );
    &_parameter_error("dst_cluster", "tagData" ) unless( $dst_cluster );

    my $resource = "/vappio/uploadTag_ws.py";
    my $req_opts = { 'tag_name' => $tag_name, 'dst_cluster' => $dst_cluster };
    $req_opts->{'src_cluster'} = ($options{'src_cluster'}) ? $options{'src_cluster'} : 'local';
    $req_opts->{'expand'} = $options{'expand'} if( $options{'expand'} );
    return $self->_make_request( $resource, $req_opts );
}
sub downloadTag {
    my ($self, $src_cluster, $tag_name, %options ) = @_;
    &_parameter_error("tag_name", "tagData") unless( $tag_name );
    &_parameter_error("src_cluster", "tagData" ) unless( $src_cluster );

    my $req_opts = { 'src_cluster' => $src_cluster, 
                     'tag_name' => $tag_name };
    $req_opts->{'dst_cluster'} = ( $options{'dst_cluster'} ) ? $options{'dst_cluster'} : 'local';
    $req_opts->{'expand'} = $options{'expand'} if( $options{'expand'} );
    my $resource = "/vappio/downloadTag_ws.py";
    return $self->_make_request( $resource, $req_opts );
}
sub downloadPipelineOutput {
    my ($self, $cluster_name, $pipeline_name, $output_dir, %options) = @_;
    &_parameter_error("cluster_name", "downloadPipelineOutput") unless( $cluster_name );
    &_parameter_error("pipeline_name", "downloadPipelineOutput" ) unless( $pipeline_name );
    &_parameter_error("output_dir", "downloadPipelineOutput" ) unless( $output_dir );

    my $req_opts = { 'name' => $cluster_name, 'pipeline_name' => $pipeline_name,
                     'output_dir' => $output_dir };
    $req_opts->{'overwrite'} = $options{'overwrite'} if( $options{'overwrite'} );
    my $resource = "/vappio/downloadPipelineOutput_ws.py";
    return $self->_make_request( $resource, $req_opts );
}
#################### PIPELINES ####################
sub pipelineStatus {
    my ($self, $pipeline, %options) = @_;
    my $req_opts = {};
    if( ref( $pipeline ) eq 'ARRAY' ) {
        $req_opts->{'pipelines'} = $pipeline;
    } else {
        $req_opts->{'pipelines'} = [ $pipeline ];
    }
    my $name = "local";
    $name = $options{'name'} if( $options{'name'} );
    $req_opts->{'name'} = $name;
    my $resource = "/vappio/pipelineStatus_ws.py";
    return $self->_make_request( $resource, $req_opts );
}
sub runPipeline {
    my ($self, $cluster_name, $pipeline_name, $pipeline_type, %options) = @_;
    &_parameter_error("cluster_name", "tagData") unless( $cluster_name );
    &_parameter_error("pipeline_name", "tagData" ) unless( $pipeline_name );
    &_parameter_error("pipeline_type", "tagData" ) unless( $pipeline_type );

    my $resource = "/vappio/runPipeline_ws.py";
    my $req_opts = { 'pipeline' => $pipeline_type, 
                     'pipeline_name' => $pipeline_name,
                     'name' => $cluster_name,
                     'args' => \%options
                 };
    return $self->_make_request( $resource, $req_opts );    
}

#################### INTERNAL ####################
sub url {
    my ($self, $url) = @_;
    if( $url ) {
        $self->{'_url'} = $url;
    }
    return $self->{'_url'};
}
sub ua {
    my ($self, $ua) = @_;
    if( $ua ) {
        $self->{'_ua'} = $ua;
    }
    return $self->{'_ua'};
}
sub _make_request {
    my ($self, $resource, $options) = @_;
    my $res = $self->ua->request( POST $self->url.$resource, 
                                  ['request' => to_json($options)] );
    return &_get_response( $res );
}
sub _get_response {
    my ($res) = @_;
    my $test = $res->decoded_content;
    my $tmp = from_json( $test );
    my ($suc, $retval) = @{$tmp};
    return ($suc, $retval);
}
sub _parameter_error {
    my ($param_name, $method) = @_;
    die("Parmeter $param_name is required for subroutine $method");
}

1;
