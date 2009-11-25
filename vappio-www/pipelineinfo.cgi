#!/usr/bin/perl

use strict;

use CGI qw(:standard);
use DateTime;
use Date::Manip; 

print header('application/x-json');
print `find /mnt/harvesting/testproject/ -name "pipeline.xml" -exec ./pipeline2table.pl {} \\; | ./table2JSON.pl pipelineid,state,componenttype,componentname,xml`;
