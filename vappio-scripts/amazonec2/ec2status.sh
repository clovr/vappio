#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
source $vappio_scripts/amazonec2/ec2_config.sh
##

#input
#INSTANCE        i-9628f0ff      ami-79e30710    ec2-67-202-30-19.compute-1.amazonaws.com        domU-12-31-39-00-48-36.compute-1.internal       running devel1  0         m1.small 2008-08-16T18:56:12+0000        us-east-1b

#output
#$publicip $privateip $status $type $time 

$EC2_HOME/bin/ec2-describe-instances | grep INSTANCE | perl -ne 'chomp;split(/\t/);print "$_[3]\t$_[4]\t$_[5]\t$_[9]\t$_[10]\n"';
