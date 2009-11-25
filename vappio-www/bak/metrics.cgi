#!/usr/bin/perl

use strict;
use CGI qw(:standard);
print header();
print `hostname -f > hostname.txt`;
print `./qhost2html.pl >  qhost.txt`;
print `./ec2status.pl >  ec2status.txt`;
print `date > lastrun.txt`;
