#!/usr/bin/perl

use strict;

use CGI qw(:standard);

print header();

my $host = param('host');
#Add administrative host to SGE
my $SGE_ROOT='/opt/sge';
my $ARCH=`$SGE_ROOT/util/arch`;
$ARCH=~s/\s+$//;
my $SGE_ROOT_BIN="/opt/sge/bin/$ARCH/";

# This environmental variable must be set or qconf will fail
$ENV{'SGE_ROOT'}="$SGE_ROOT";
#print "$SGE_ROOT_BIN/qconf -ah $host";
print `$SGE_ROOT_BIN/qconf -ah $host &> /tmp/add_host.out`;
# return a list of admin hosts
print `$SGE_ROOT_BIN/qconf -sh`;
#print "\ni$>\t$(\n";
