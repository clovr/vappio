#!/usr/bin/perl

use strict;
my $SGE_ROOT='/opt/sge';
my $SGE_ROOT_BIN='$SGE_ROOT/bin/lx24-x86/';
$ENV{'SGE_ROOT'}="$SGE_ROOT";

my @lines=`$SGE_ROOT_BIN/qhost -q -j`;
print "<pre><code>";
foreach my $line (@lines){
	chomp $line;
	$line =~ s/\s/&nbsp;/g;
	$line =~ s/^([^&]+)(&nbsp;)+lx/<a href='\/ganglia\/?h=$1.compute-1.internal&c=Grid+V1'>$1<\/a>$2lx/;
	print $line,"<br>\n";
}
print "</code></pre>";
