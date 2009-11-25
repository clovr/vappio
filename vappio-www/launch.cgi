#!/usr/bin/perl

use strict;
use CGI qw(:standard);

print header();
my $cmd="/opt/vappio-scripts/amazonec2/launch_instances.sh ".param('node-role')." ".param('count')." ".param('node-type');
`date >> /var/vappio_runtime/launch.log`;
`echo $cmd >> /var/vappio_runtime/launch.log`;
`$cmd >> /var/vappio_runtime/launch.log`
