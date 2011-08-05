#!/bin/bash
# Simple script to give you the diag env to run ec2 commands.
# Takes 2 parameters, first is path to cert file, second is path to key file

export EC2_CERT=$1
export EC2_PRIVATE_KEY=$2

export EC2_URL=https://nimbus.diagcomputing.org:8443/wsrf/services/ElasticNimbusService

export EC2_JVM_ARGS="-Djavax.net.ssl.trustStore=/tmp/jssecacerts"

export EC2_HOME=/opt/ec2-api-tools-1.3-57419

export PATH=$EC2_HOME/bin:$PATH
