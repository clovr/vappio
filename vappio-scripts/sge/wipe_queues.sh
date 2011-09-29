#/bin/bash
##Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh
##

myhostname=`vhostname`

# Remove all submit hosts
hosts=`qconf -ss`
for p in $hosts
do
    qconf -ds $p 
done

# Remove all queues
for p in `qconf -sql`
do
    qconf -dq $p
done

#kill exec hosts
qconf -kej $myhostname # shutdown execution daemon(s)
hosts=`qconf -sel`
for p in $hosts
do
    qconf -de $p
done

# remove all admin hosts
hosts=`qconf -sh`
for p in $hosts
do
    qconf -dh $p
done

qconf -dprj global
