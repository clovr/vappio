#!/bin/sh
export SGE_ROOT=/opt/sge
#cleanup old install
rm -rf $SGE_ROOT/default
adduser sgeadmin
chown -R sgeadmin $SGE_ROOT
pushd $SGE_ROOT
./inst_sge -m -x -auto /opt/vappio-scripts/sge/vappio_sge.conf
popd
rm -f /etc/init.d/sgemaster

ln -s /opt/sge/default/common/sgemaster /etc/init.d/sgemaster

ARCH=`$SGE_ROOT/util/arch`
$SGE_ROOT/bin/$ARCH/qconf -am apache
$SGE_ROOT/bin/$ARCH/qconf -ao guest
cp drmaa.jar $SGE_ROOT/lib
