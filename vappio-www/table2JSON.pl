#!/usr/bin/perl

#2 column tab delimeted table
#table2JSON "id,name" < table.txt
#Example
#./pipelines2table.pl /usr/local/projects/xantho/ergatis/workflow/runtime/pipeline/461/pipeline.xml | ./table2JSON.pl "id,state,type,name,xml"

use strict;
use Data::Dumper;
use JSON 2.0;

die "USAGE: tabl2JSON.pl 'field1,field2,...,fieldn' < tabdelim.txt" if(!$ARGV[0]);

my @fields = split(",",$ARGV[0]);

my @output;
while(my $line=<STDIN>){
	chomp $line;
    my @elts = split(/\t/,$line);
    my $i=0;
    my %hash = map { $fields[$i++] => $_ } @elts;
    push @output,\%hash;
}
#print Dumper(\@output);

print to_json(\@output);
