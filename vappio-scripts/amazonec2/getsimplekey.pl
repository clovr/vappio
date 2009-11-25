#!/usr/bin/perl

# This software code is made available "AS IS" without warranties of any        
# kind.  You may copy, display, modify and redistribute the software            
# code either by itself or as incorporated into your code; provided that        
# you do not remove any proprietary notices.  Your use of this software         
# code is at your own risk and you waive any claim against Amazon               
# Digital Services, Inc. or its affiliates with respect to your use of          
# this software code. (c) 2006-2007 Amazon Digital Services, Inc. or its             
# affiliates.          

use strict;
use warnings;
use lib '/opt/s3';
use S3;
use S3::AWSAuthConnection;
use S3::QueryStringAuthGenerator;

my $AWS_ACCESS_KEY_ID = `cat /root/AWS_ACCESS_KEY_ID`;
chomp $AWS_ACCESS_KEY_ID;
my $AWS_SECRET_ACCESS_KEY = `cat /root/AWS_SECRET_ACCESS_KEY`;
chomp $AWS_SECRET_ACCESS_KEY;

# For subdomains (bucket.s3.amazonaws.com), the bucket name must be lowercase
# since DNS is case-insensitive.
my $BUCKET_NAME = lc "$ARGV[0]";

my $conn =
    S3::AWSAuthConnection->new($AWS_ACCESS_KEY_ID, $AWS_SECRET_ACCESS_KEY);
my $generator =
    S3::QueryStringAuthGenerator->new($AWS_ACCESS_KEY_ID, $AWS_SECRET_ACCESS_KEY);


my $response = $conn->get($ARGV[0],$ARGV[1]);
my $metadata = $response->object->metadata;
my $title = $metadata->{title};

print $response->object->data;



