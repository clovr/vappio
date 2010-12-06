#!/usr/bin/perl

eval 'exec /usr/bin/perl  -S $0 ${1+"$@"}'
    if 0; # not running under some shell
    
=head1 NAME

JSON_command_summary.pl - creates and writes to disk command summary in JSON format

=head1 SYNOPSIS
	
	./JSON_command_summary.pl
		--xml_file=/path/to/xml/file
		[--log_file=/path/to/log/file
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
my $START_TIME = 'start_time';
my $END_TIME = 'end_time';
my $STATE = 'state';
my $COUNT = 'count';
my $count = 1;

############################################
#              MAIN PROGRAM                #
############################################

my $root = {};
$$root{$PIPELINE}{$CMDS} = {};
$$root{$PIPELINE}{$CMPS} = {};

my $options = parse_options();
process_file( $$options{'xml_file'} );
#print encode_json( $root );
my $data = {};
add_component_or_command_info( $$root{$PIPELINE}{$CMPS}, $CMPS );
add_component_or_command_info( $$root{$PIPELINE}{$CMDS}, $CMDS );
print encode_json( $data );
exit(0);

############################################
#             END OF MAIN                  #
############################################

############################################
#            SUB ROUTINES                  #
############################################

sub add_component_or_command_info {
	my ($node, $domain) = @_;
	foreach my $key (keys %$node) {
		$$data{$domain}{$key}{$START_TIME} = $$node{$key}{$START_TIME};
		$$data{$domain}{$key}{$END_TIME} = $$node{$key}{$END_TIME};
		$$data{$domain}{$key}{$ELAPSED_TIME} = $$node{$key}{$ELAPSED_TIME};
		$$data{$domain}{$key}{$STATE} = $$node{$key}{$STATE};
		$$data{$domain}{$key}{$CPU_TIME} = $$node{$key}{$CPU_TIME};
		$$data{$domain}{$key}{$COUNT} = $$node{$key}{$COUNT} if($domain eq $CMDS);
		#get_req_info($$node{$key}{$domain}) if( $domain eq $CMPS );
	}
}

sub parse_options {
	my %options = ();
	GetOptions( \%options, 
		'xml_file|x=s',
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
        print "processing $path\n";
    
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
	$$node{$ELAPSED_TIME} = $end_time - $start_time;
	$$node{$STATE} = $state;
	$$node{$CPU_TIME} += $end_time - $start_time if( $is_command );
	if($end_time && $start_time) {
		return $end_time - $start_time;
	} else {
		return 0;
	}
}
