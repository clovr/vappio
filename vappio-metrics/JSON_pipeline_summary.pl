#!/usr/bin/perl

eval 'exec /usr/bin/perl  -S $0 ${1+"$@"}'
    if 0; # not running under some shell
    
=head1 NAME

JSON_command_summary.pl - creates and writes to disk command summary in JSON format

=head1 SYNOPSIS
	
	./JSON_command_summary.pl
		--xml_file|-x=/path/to/xml/file
		[--cmds_time_info| -c
		 --log_file=/path/to/log/file
		 --debug=<debug level>
		 --help]
				 
=head1 PARAMETERS

B<--xml_file, -x>
	The root xml file to build command summary
	The root xml file can contain nested xml files

B<--log_file, -l>
	Optional. Log file.
	
B<--debug, -d>
	Optional. Debug level.
	
B<--help>
	Prints this documentation
	

=head1 Description

Goes through the xml file and gathers stats of each component, command (includes, elapsed_time,
cpu_hours, status etc)

=head1 INPUT

Input is an root xml file or an xml file that has commands. Perl file will go through and gathers 
information from the nested xml files

=head1 OUTPUT

JSON structure of pipeline stats will be written to disk

pipeline : {
		state : complete,
		elapsed_time : --,
		cpu_hours : --,
		start_time : --,
		end_time : -- , 
		components : {
			comp_1 : {
				state: ..,
				components : {},
				commands : {}
			}, comp_2 : {
		
		},
		 commands : {
			command_1 : {
		
			}, command_2 : {
		
			}, ...
		}
	}

=head1 AUTHOR

	Mahesh Vangala
	mvangala@som.umaryland.edu
	vangalamaheshh@gmail.com
	
=cut

############################################
#        LIBRARIES & PRAGMAS               #
############################################

use strict;
use warnings;
use JSON::PP;
use Date::Manip;
use XML::Twig;
use Pod::Usage;
use Getopt::Long qw(:config no_ignore_case no_auto_abbrev pass_through);

############################################
#            GLOBALS VARS                  #
############################################

my ($TRUE, $FALSE) = (1,0);
my $PIPELINE_TOKEN = 'start pipeline:';
my $PIPELINE = 'pipeline';
my $CMDS = 'commands';
my $CMPS = 'components';
my $CPU_TIME = 'cpu_time';
my $ELAPSED_TIME = 'elapsed_time';
my $ACTUAL_ELAPSED_TIME = 'actual_elapsed_time';
my $START_TIME = 'start_time';
my $END_TIME = 'end_time';
my $STATE = 'state';
my $COUNT = 'count';
my $count = 1;
my $TIME_INFO = 'time_info';

############################################
#              MAIN PROGRAM                #
############################################

my $root = {};
$$root{$PIPELINE}{$CMDS} = {};
$$root{$PIPELINE}{$CMPS} = {};

my $options = parse_options();
process_file( $$options{'xml_file'} );
my $data = {};
$data = add_component_or_command_info($data, $$root{$PIPELINE}{$CMPS}, $CMPS, $TRUE, undef );
$data = add_component_or_command_info($data, $$root{$PIPELINE}{$CMDS}, $CMDS, $TRUE, undef );
$$data{$CMDS} = add_actual_elapsed_time( $$data{$CMDS} );

if( exists $$options{'cmds_time_info'} ) {
	print encode_json( sorted( add_pipeline_info( $data, $root ) ) );
} else {
	my $data_without_time_info = {};
	$data_without_time_info = add_component_or_command_info( $data_without_time_info, $$root{$PIPELINE}{$CMPS}, $CMPS, $FALSE, undef );
	$data_without_time_info = add_component_or_command_info( $data_without_time_info, $$root{$PIPELINE}{$CMDS}, $CMDS, $FALSE, $data );
	print encode_json( sorted( add_pipeline_info( $data_without_time_info, $root ) ) );
}

exit(0);

############################################
#             END OF MAIN                  #
############################################

############################################
#            SUB ROUTINES                  #
############################################

sub add_pipeline_info {
	my ($copy_to, $copy_from) = @_;
	$$copy_to{$CMPS}{$PIPELINE}{$START_TIME} = $$copy_from{$PIPELINE}{$START_TIME};
	$$copy_to{$CMPS}{$PIPELINE}{$END_TIME} = $$copy_from{$PIPELINE}{$END_TIME};
	$$copy_to{$CMPS}{$PIPELINE}{$CPU_TIME} = $$copy_from{$PIPELINE}{$CPU_TIME};
	$$copy_to{$CMPS}{$PIPELINE}{$ELAPSED_TIME} = $$copy_from{$PIPELINE}{$ELAPSED_TIME};
	$$copy_to{$CMPS}{$PIPELINE}{$STATE} = $$copy_from{$PIPELINE}{$STATE};
	return $copy_to;
}

sub add_actual_elapsed_time {
	my ($command_node) = @_;
	foreach my $key( keys %$command_node ) {
		$$command_node{$key}{$ACTUAL_ELAPSED_TIME} = get_actual_elapsed_time( $$command_node{$key}{$TIME_INFO} );
	}
	return $command_node;
}

sub get_actual_elapsed_time {
	my ($ref_time_array) = @_;
	my ($actual_elapsed_time, $counter, $start_time_info, $end_time_info) = (0, 0, undef, undef);
	my ($start_flag, $end_flag) = ( $TRUE, $FALSE );
	foreach my $time( @$ref_time_array ) {
		my $time_only;
		if( $time =~ /(.+)=(.+)/ ) {
			$time_only = $2;
			$1 eq $START_TIME ? $counter++ : $counter--;
		}
		if( $counter == 1 && $start_flag ) {
			$start_time_info = $time_only;
			$start_flag = $FALSE;
			$end_flag = $TRUE;
		} elsif( $counter == 0 && $end_flag ) {
			$end_time_info = $time_only;
			my $ssecs = UnixDate( $start_time_info, "%s" );
			my $esecs = UnixDate( $end_time_info, "%s" );
			print STDERR "Bad $start_time_info $end_time_info $ssecs - $esecs\n" if(!$ssecs || !$esecs);
			$actual_elapsed_time += $esecs - $ssecs; 
			$start_flag = $TRUE;
			$end_flag = $FALSE;
			($start_time_info, $end_time_info) = (undef, undef);
		}
	}
	return $actual_elapsed_time;
}

sub sorted {
	my ($data) = @_;
	my $sorted_keys;
	foreach my $top_key( keys %$data ) {
		@{$$sorted_keys{$top_key}} =  sort { $$data{$top_key}{$b}{$CPU_TIME} <=> $$data{$top_key}{$a}{$CPU_TIME} } keys %{$$data{$top_key}};
	}
	my $sorted_data;

	foreach my $top_key ( keys %$data ) {
		foreach my $sorted_key ( @{$$sorted_keys{$top_key}} ) {
			push @{$$sorted_data{$top_key}}, { $sorted_key => $$data{$top_key}{$sorted_key} };
		}
	}
	return $sorted_data;
}


sub add_component_or_command_info {
	my ($data, $node, $domain, $add_time_info, $node_with_time_info) = @_;
	foreach my $key (keys %$node) {
		$$data{$domain}{$key}{$START_TIME} = $$node{$key}{$START_TIME};
		$$data{$domain}{$key}{$END_TIME} = $$node{$key}{$END_TIME};
		$$data{$domain}{$key}{$ELAPSED_TIME} = $$node{$key}{$ELAPSED_TIME};
		$$data{$domain}{$key}{$STATE} = $$node{$key}{$STATE};
		$$data{$domain}{$key}{$CPU_TIME} = $$node{$key}{$CPU_TIME};
		$$data{$domain}{$key}{$COUNT} = $$node{$key}{$COUNT} if($domain eq $CMDS);
		@{$$data{$domain}{$key}{$TIME_INFO}} = sort by_time @{$$node{$key}{$TIME_INFO}} if( $domain eq $CMDS && $add_time_info );
		$$data{$domain}{$key}{$ACTUAL_ELAPSED_TIME} = $$node_with_time_info{$domain}{$key}{$ACTUAL_ELAPSED_TIME} if( $domain eq $CMDS && !$add_time_info );
		#get_req_info($$node{$key}{$domain}) if( $domain eq $CMPS );
	}
	return $data;
}

sub by_time {
	my ($a_token, $b_token, $a_time, $b_time);
	if( $a =~ /(.+)=(.+)/ ) {
		$a_token = $1;
		$a_time = $2;
	}
	if( $b =~ /(.+)=(.+)/ ) {
		$b_token = $1;
		$b_time = $2;
	}
	my $a_time_in_seconds = UnixDate( $a_time, "%s" );
	my $b_time_in_seconds = UnixDate( $b_time, "%s" );
	$a_time_in_seconds <=> $b_time_in_seconds;
}

sub parse_options {
	my %options = ();
	GetOptions( \%options, 
		'xml_file|x=s',
		'cmds_time_info|c',
		'log_file|l:s',
		'debug|d:s',
		'help|h' ) || pod2usage();
	
	if ( $options{'help'} ) {
		pod2usage( {
			-exitval => 1,
			-verbose => 1,
			-output => \*STDOUT
		} );
	}
	
	return \%options;
}

sub process_file {
	my $path = shift;
            
    	my $fh = get_conditional_read_fh($path);

    	if ( $fh ) {
        	my $t = XML::Twig->new( twig_roots => { 'commandSet' => \&process_root } );

        	$t->parse( $fh ); 
    	}	
}

sub process_root {
	my ($twig, $element) = @_;
	if($element->first_child('name')->text() eq $PIPELINE_TOKEN) {
		set_time_and_state_info( $element, $$root{$PIPELINE} );
		$$root{$PIPELINE}{$CPU_TIME} = 0;
		foreach my $commandSet( $element -> children('commandSet') ) {
			my $name;
			unless( $commandSet -> first_child('name') -> text() ) {
				$name = $count++;
			} else {
				$name = $commandSet -> first_child('name') -> text();
			}
			$$root{$PIPELINE}{$CMPS}{$name}{$CMPS} = {};
			$$root{$PIPELINE}{$CMPS}{$name}{$CMDS} = {};
			$$root{$PIPELINE}{$CMPS}{$name}{$CPU_TIME} = 0;
			set_time_and_state_info( $commandSet, $$root{$PIPELINE}{$CMPS}{$name} );
			$$root{$PIPELINE}{$CPU_TIME} += process( $commandSet, $$root{$PIPELINE}{$CMPS}{$name}{$CMPS}, $$root{$PIPELINE}{$CMPS}{$name}{$CMDS}, $$root{$PIPELINE}{$CMPS}{$name} );
			my $file = $commandSet -> first_child_text('fileName');
	                my $fh = get_conditional_read_fh($file);
	                if ( $fh ) {
        	                my $t = XML::Twig->new( twig_roots => { 'commandSetRoot' => sub {
                	                my ($new_twig, $new_elt) = @_;
                        	        $$root{$PIPELINE}{$CPU_TIME} += process(  $new_elt, $$root{$PIPELINE}{$CMPS}{$name}{$CMPS}, $$root{$PIPELINE}{$CMPS}{$name}{$CMDS}, $$root{$PIPELINE}{$CMPS}{$name} );
                       		 } } );

               	        	 $t->parse( $fh );
               		 }

		}

		foreach my $command ( $element->children('command') ) {
                	$$root{$PIPELINE}{$CMDS}{$command -> first_child('name')->text()}{$COUNT}++;
                	$$root{$PIPELINE}{$CPU_TIME} += set_time_and_state_info( $command, $$root{$PIPELINE}{$CMDS}{$command -> first_child('name') -> text()}, $TRUE );
        	}

	}
}

sub process {
	my ($elt, $component_node, $command_node, $parent_node) = @_;	
	
        foreach my $commandSet( $elt->children('commandSet') ) {
	
		my $name;

		unless( $commandSet -> first_child('name')-> text() ) {
			$name = $count++;
		} else {
			$name = $commandSet -> first_child('name') -> text();
		}
		
		$$component_node{$name}{$CMPS} = {};
		$$component_node{$name}{$CMDS} = {};
		$$component_node{$name}{$CPU_TIME} = 0;
		set_time_and_state_info( $commandSet, $$component_node{$name} );
		$$parent_node{$CPU_TIME} += process( $commandSet, $$component_node{$name}{$CMPS}, $$component_node{$name}{$CMDS}, $$component_node{$name} );

		my $file = $commandSet -> first_child_text('fileName');
		my $fh = get_conditional_read_fh($file);
		if ( $fh ) {
        		my $t = XML::Twig->new( twig_roots => { 'commandSetRoot' => sub {
        			my ($new_twig, $new_elt) = @_;
        			$$parent_node{$CPU_TIME} += process( $new_elt, $$component_node{$name}{$CMPS}, $$component_node{$name}{$CMDS}, $$component_node{$name} );
        		} } );
	
        		$t->parse( $fh ); 
    		} 		
		
	}

	foreach my $command( $elt->children('command') ) {
        	$$command_node{$command -> first_child('name')->text()}{$COUNT}++;
                set_time_and_state_info( $command, $$command_node{$command -> first_child('name')->text()}, $TRUE );
                $$root{$PIPELINE}{$CMDS}{$command -> first_child('name')->text()}{$COUNT}++;
                $$parent_node{$CPU_TIME} += set_time_and_state_info( $command, $$root{$PIPELINE}{$CMDS}{$command -> first_child('name') -> text()}, $TRUE );
        }

	return $$parent_node{$CPU_TIME};

} 

sub get_conditional_read_fh {
	my $path = shift;
	my $fh;
	my $found = 0;
    
    	if ( -e $path ) {
        	$found = 1;
    
	    ## auto-handle gzipped files
	} elsif (! -e $path && -e "$path.gz") {
        	$path .= '.gz';
        	$found = 1;
    	} 
    
    	if (! $found ) {
        ## we can't find the file.  just return an empty file handle. 
        ##  the process sub is OK with this.
        	return $fh;
    	}

    	if ( $path =~ /\.gz$/ ) {
        	open($fh, "<:gzip", $path) || die "can't read file $path: $!";
    	} else {
        	open($fh, "<$path") || die "can't read file $path: $!";
    	}
    
    	return $fh;
}


sub set_time_and_state_info {
	my ($command, $node, $is_command) = @_;
	my ($start_time, $end_time, $elapsed_time);
    
    	## make sure we can at least get start time
    	if (! $command->first_child('startTime') ) {
        	$start_time = 0;
    	} else {
		$start_time = UnixDate(ParseDate( $command -> first_child('startTime') -> text ), "%s");
	}

    	my $state = $command->first_child('state')->text;
    	
    	## end time may not exist (if running, for example)
    	if (! $command->first_child('endTime') ) {
        	$end_time = 0;
   	} else {
		$end_time = UnixDate(ParseDate( $command -> first_child('endTime') -> text ), "%s");
	}
	
	$$node{$START_TIME} = UnixDate(&ParseDateString("epoch $start_time"), "%c") unless( $$node{$START_TIME} );
	$$node{$END_TIME} = UnixDate(&ParseDateString("epoch $end_time"), "%c");
	$$node{$ELAPSED_TIME} = UnixDate( $$node{$END_TIME}, "%s" ) - UnixDate( $$node{$START_TIME}, "%s" );
	$$node{$STATE} = $state;
	$$node{$CPU_TIME} += $end_time - $start_time if( $is_command );
	push @{$$node{$TIME_INFO}}, ( $START_TIME . "=" . UnixDate(&ParseDateString("epoch $start_time"), "%c"), $END_TIME . "=" . UnixDate(&ParseDateString("epoch $end_time"), "%c") ) if( $is_command );
	if($end_time && $start_time) {
		return $end_time - $start_time;
	} else {
		return 0;
	}
}
