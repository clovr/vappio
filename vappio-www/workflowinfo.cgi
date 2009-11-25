#!/usr/bin/perl

use strict;

use CGI qw(:standard);
use DateTime;
use Date::Manip; 

my $count=param('count')||2000;
my $xml=param('xml')||2000;
print header('application/x-json');
print `./xml2table.pl $xml | grep -v -e '^0' | sort -n | tail -$count | ./table2JSON.pl seconds,id,name,executable,state,startTime,endTime,runtime,filename,executionHost,gridID`;

