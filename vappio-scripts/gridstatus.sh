#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

$vappio_scripts/sgestatus.pl > $vappio_runtime/sgestatus.txt 
$vappio_scripts/amazonec2/ec2status.sh > $vappio_runtime/ec2status.txt 

