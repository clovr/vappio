#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

myhostname=`hostname -f`

# Remove all submit hosts
hosts=`$SGE_ROOT/bin/$ARCH/qconf -ss`
for p in $hosts
do
    $SGE_ROOT/bin/$ARCH/qconf -ds $p 
done

# Remove all queues
for p in `$SGE_ROOT/bin/$ARCH/qconf -sql`
do
    $SGE_ROOT/bin/$ARCH/qconf -dq $p
done

#kill exec hosts
$SGE_ROOT/bin/$ARCH/qconf -kej $myhostname # shutdown execution daemon(s)
hosts=`$SGE_ROOT/bin/$ARCH/qconf -sel`
for p in $hosts
do
    $SGE_ROOT/bin/$ARCH/qconf -de $p
done

# remove all admin hosts
hosts=`$SGE_ROOT/bin/$ARCH/qconf -sh`
for p in $hosts
do
    $SGE_ROOT/bin/$ARCH/qconf -dh $p
done

$SGE_ROOT/bin/$ARCH/qconf -dprj global
