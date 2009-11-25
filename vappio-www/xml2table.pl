#!/usr/bin/perl -w

#Reads workflow XML
#Writes table with columns totseconds,id,name,executable,state,startTime,endTime,totminutes,filename
#
#Examples
#100 slowest commands
#./xml2table.pl pipeline.xml | sort -n | tail -100
#1000 slowest commands output in JSON format
#./xml2table.pl /usr/local/projects/xantho/ergatis/workflow/runtime/pipeline/461/pipeline.xml | sort -n | tail -1000 | ./table2JSON.pl "seconds,id,name,executable,state,startTime,endTime,runtime,filename"

use strict;
use Date::Manip;
use XML::Twig;

my %cmds;

my $source_file = shift || die "pass an XML file to parse\n";

process_file( $source_file );

my $total = 0;

foreach my $cmd ( keys %cmds ) {
    $total += $cmds{$cmd};
    print STDERR "\t$cmd - $cmds{$cmd}s\n";
}

print STDERR "\ntotal CPU time: ${total}s\n\n";

exit();


my @currfiles;
my $hosts = {};
sub process_file {
    my $path = shift;
    
    push @currfiles,$path;
    print STDERR "processing $path\n";
    
    my $fh = get_conditional_read_fh($path);

    if ( $fh ) {
        my $t = XML::Twig->new(
                           twig_roots => {
                               'command' => sub {
                                   my ($t, $elt) = @_;
				   my $time = time_info($elt);
				   my ($execc) = ($elt->first_child_text('executable') =~ /\/([^\/]+)$/);
				   my ($file) = ($currfiles[$#currfiles] =~ /\/([^\/]+\/[^\/]+\/[^\/]+)$/);
				   my @elts = ($time,
					       $elt->first_child_text('id')||-1,
					       $elt->first_child_text('name')||'',
					       $execc||'',
					       $elt->first_child_text('state')||'',
					       $elt->first_child_text('startTime')||'',
					       $elt->first_child_text('endTime')||'',
					       Delta_Format(ParseDateDelta($time),1,"%mhm%sds")||'',
					       $file||''
					       );

				   my $host='';
				   my $gridid='';
				   if($currfiles[$#currfiles] =~ /(i\d+\/g\d+)/){
				       $host = $hosts->{$1}->{'executionHost'} || '';
				       $gridid = $hosts->{$1}->{'gridID'} if(exists $hosts->{$1}->{'gridID'}) || '';
				   }
				   print join("\t",@elts,$host,$gridid),"\n";
				   
                               },
                               'commandSet' => sub {
                                   my ($t, $elt) = @_;
				   my $currfilename = $elt->first_child_text('fileName');
				   if($currfilename){
				       my ($remotexml) = ($currfilename =~ /(i\d+\/g\d+)/);
				       my $dcespec = $elt->first_child('dceSpec');
				       if($dcespec && $dcespec->first_child('executionHost') && $dcespec->first_child('gridID')){
					   $hosts->{$remotexml}->{'executionHost'} = $dcespec->first_child_text('executionHost');
					   $hosts->{$remotexml}->{'gridID'} = $dcespec->first_child_text('gridID');
				       }
				       process_file( $currfilename );
				   }
                               },
                           },);

        $t->parse( $fh ); 
	pop @currfiles;
    } else {
    }
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


sub time_info {
    my $command = shift;
    
    ## make sure we can at least get start time
    if (! $command->first_child('startTime') ) {
        return 0;
    }
    
    my $state = $command->first_child('state')->text;
    my $start_time_obj = ParseDate( $command->first_child('startTime')->text );
    my $start_time     = UnixDate( $start_time_obj, "%c" );
    
    my ($end_time_obj, $end_time);
    ## end time may not exist (if running, for example)
    if ( $command->first_child('endTime') ) {
        $end_time_obj   = ParseDate( $command->first_child('endTime')->text );
        $end_time       = UnixDate( $end_time_obj, "%c" );
    }

    ## doing it here manually because strftime was behaving badly (or I coded it badly)
    if ($start_time_obj) {
        my $diffstring;
        
        if ($end_time_obj) {
            $diffstring = DateCalc($start_time_obj, $end_time_obj, undef, 1);
        } else {
            $diffstring = DateCalc($start_time_obj, "now", undef, 1);
        }
        
        ## take out any non \d: characters
        $diffstring =~ s/[^0-9\:]//g;

        my @parts = split(/:/, $diffstring);
        
        ## years + months + weeks + days
        my $days = ($parts[0] * 365) + ($parts[1] * 30) + ($parts[2] * 7) + ($parts[3]);
        
        # ( days + hours + min + sec )
        return ($days * 86400) + ($parts[4] * 3600) + ($parts[5] * 60) + $parts[6];
    } else {
        return 0;
    }
}
