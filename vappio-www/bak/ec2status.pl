#!/usr/bin/perl

use strict;

$ENV{'EC2_AMITOOL_HOME'}="/opt/ec2-ami-tools-1.3-20041";
$ENV{'EC2_HOME'}="/opt/ec2-api-tools-1.3-19403";
$ENV{'EC2_PRIVATE_KEY'}="/mnt/pk-6MATML4RY432CYXZH7XW2RBBZAVBILI4.pem";
$ENV{'EC2_CERT'}="/mnt/cert-6MATML4RY432CYXZH7XW2RBBZAVBILI4.pem";
$ENV{'JAVA_HOME'}="/usr/lib/jvm/sun-java-5.0u15/jre";

#INSTANCE        i-9628f0ff      ami-79e30710    ec2-67-202-30-19.compute-1.amazonaws.com        domU-12-31-39-00-48-36.compute-1.internal       running devel1  0         m1.small 2008-08-16T18:56:12+0000        us-east-1b

#$publicip $privateip $status $type $time 
my @lines=`$ENV{'EC2_HOME'}/bin/ec2-describe-instances`;
foreach my $line (@lines){
		chomp $line;
		if($line =~ /INSTANCE/){
			my @elts = split(/\s+/,$line);
	        chomp $line;
    	    print "$elts[3]\t$elts[4]\t$elts[5]\t$elts[8]\t$elts[9]\n";
		}
}

