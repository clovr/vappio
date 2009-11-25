#!/usr/bin/perl 

#

use strict;
use XML::Twig;
use Data::Dumper;
use CGI qw(:standard);

my $xml = $ARGV[0];
my($pipelineid) = ($xml =~ /(\d+)\/pipeline\.xml/);
my $cname;
my $state;
my @output;

my $t = XML::Twig->new(twig_roots => {
    'commandSet' => sub {
	my($t,$elt) = @_;
	my $cname = $elt->first_child_text('name');
	my($ctype) = ($cname =~ /(\w+)\.\w+/);
	my $state = $elt->first_child_text('state');
	if($elt->first_child('command') && $elt->first_child('command')->first_child_text('name') eq 'replace_config_keys'){
	    push @output,[$pipelineid,
			  $state,
			  $ctype,
			  $cname,
			  "<a href='#' onClick='Ext.v_showwfxml(\"$xml\")'>$xml</a>"
			  ];
	}
    }
});
		   
if($pipelineid){
    my $fh = get_conditional_read_fh($xml);
    $t->parse( $fh ); 
}

#print Dumper(\@output);
foreach my $row (@output){
    print join("\t",@$row),"\n";
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

