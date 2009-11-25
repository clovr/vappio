#!/usr/bin/perl

use strict;

use JSON;
use CGI qw(:standard);

my @sgestatus = `./qhost2table.pl`;
my @ec2status = `./ec2status.pl`;

my @status;
my $hosts = {};

foreach my $l (@ec2status){
	chomp $l;
	my ($publicip,$privateip, $status, $type, $time) = split(/\t/,$l);
	$hosts->{$privateip}->{'privateip'} = $privateip; 
	$hosts->{$privateip}->{'publicip'} = $publicip; 
	$hosts->{$privateip}->{'status'} = $status; 
	$hosts->{$privateip}->{'type'} = $type; 
	$hosts->{$privateip}->{'time'} = $time; 

}
foreach my $l (@sgestatus){
	chomp $l;
	my ($ip,$type, $queue, $idle, $job, $load, $memtot, $memused, $cpus) = split(/\t/,$l);
	my $privateip = $ip.".compute-1.internal";
	push @status,{
		"publicip"=>$hosts->{$privateip}->{'publicip'},
		"privateip"=>$hosts->{$privateip}->{'privateip'},
		"status"=>$hosts->{$privateip}->{'status'},
		"type"=>$hosts->{$privateip}->{'type'},
		"role"=>$type,
		"uptime"=>$hosts->{$privateip}->{'time'},
		"queue"=>$queue,
		"idle"=>$idle,
		"job"=>$job,
		"load"=>$load,
		"memtot"=>$memtot,
		"memused"=>$memused,
		"cpus"=>$cpus
	};
}
#my @statustest = ({'x'=>'1.1.1','a'=>'1.1.1'});

print header('application/x-json');
my $coder = JSON::PP->new->allow_nonref;
#$coder->canonical(1);
print $coder->encode (\@status);

exit;

