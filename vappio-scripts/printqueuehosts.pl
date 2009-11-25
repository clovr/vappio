#!/usr/bin/perl

use strict;

my $queue = $ARGV[0];
die "USAGE: printqueuehosts.pl [queue_name]" if(!defined $queue);
my $cmd = "$ENV{'SGE_ROOT'}/bin/$ENV{'ARCH'}/qconf -sq $queue";
#print "Running $cmd\n";
my @out = `$cmd`;
my @hosts;
my $hostlist=0;
my $hostline = '';
foreach my $line (@out){
chomp $line;
# Note: it's possible for multiple hosts to be listed on a line!
if($line =~ /^hostlist/){
	if($line =~ /NONE/){
		last;
	#print "NONE\n";	
	}	
	else{
		$hostlist=1;
	        $line =~ s/\\//g;
		#my($x,$host) = split(/\s+/,$line);
		#push @hosts,$host;
		$hostline .= $line;
	#print "host:$host\n";
	}
}elsif($line =~ /^\w+/){
	last if($hostlist==1);
	$hostlist=0;
}elsif($hostlist==1){
	$line =~ s/\\//g;
	#$line =~ s/\s+//g;
	#push @hosts,$line;
	$hostline.=$line;
}
}
@hosts = split(/\s+/,$hostline);
shift @hosts; #remove leading "hostlist"
if(scalar(@hosts)){print join(' ',@hosts),"\n";}
