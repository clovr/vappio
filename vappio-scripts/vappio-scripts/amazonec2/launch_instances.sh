#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
source $vappio_scripts/amazonec2/ec2_config.sh
##
##
role=$1
count=$2
type=$3

amiid=`curl -f -s http://169.254.169.254/1.0/meta-data/ami-id`
master=`cat $SGE_ROOT/$SGE_CELL/common/act_qmaster`

if [ $role = "data" ]
then
	cmd="$EC2_HOME/bin/ec2-run-instances $amiid -g vappio -n $count -d MASTER_NODE=$master,DATA_NODE=localhost --instance-type=$type"
else
    cmd="$EC2_HOME/bin/ec2-run-instances $amiid -g vappio -n $count -d MASTER_NODE=$master --instance-type=$type"
fi

$cmd

