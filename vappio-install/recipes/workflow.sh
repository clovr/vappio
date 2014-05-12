#!/bin/bash
#v1 Mod with dcespec/queue support
#wget http://cb2.igs.umaryland.edu/wf_clovr.tgz
#v2,v3 mods for mkdir retry and no fatal error on idgen retry
#wget http://cb2.igs.umaryland.edu/wf_clovr_3.0vp2.tgz
#v4 mod to update FileIdGenerator to fix bug #609
#wget http://cb2.igs.umaryland.edu/wf_clovr_3.0vp4.tgz
#v5 add dir.exists() to handle mkdir bug #655
#v5.1 adds fix for premature idfile exception
#v5.2 catches exceptions during monitoring
#v5.3 (broken)
#v5.4 Fixes event.log monitoring 
#v5.5 More fixes event.log monitoring using events hash 
#v5.6 Adds ThreadPool fix from workflow SVN
#v5.7 Adds monitor respawn on exception and qsub retry
wget http://bioifx.org/wf_clovr_3.0vp5.7.tgz
tar -C / -xvzf wf_clovr_3.0vp5.7.tgz
chmod 777 /opt/workflow-sforge
#Set permissions on id file
chmod 777 /opt/workflow-sforge/idfile
chmod a+r /opt/workflow-sforge/jars/wf.jar
chown www-data:www-data /opt/workflow-sforge/idfile

#Change queue in SGE_QUEUE_CONFIG

wget http://bioifx.org/drmaa.jar
SGE_ROOT=/var/lib/gridengine
mkdir -p $SGE_ROOT/lib
cp drmaa.jar $SGE_ROOT/lib
cp drmaa.jar /opt/workflow-sforge/jars/
apt-get -y install libdrmaa1.0 libdrmaa-dev

ln -f -s /usr/lib $SGE_ROOT/lib/lx26-ia64

mkdir /tmp/$$
pushd /tmp/$$
#wget http://search.cpan.org/CPAN/authors/id/T/TH/THARSCH/Schedule-DRMAAc-0.81.tar.gz
wget http://cpan.metacpan.org/authors/id/T/TH/THARSCH/Schedule-DRMAAc-0.81.tar.gz
tar xvzf Schedule-DRMAAc-0.81.tar.gz 
cd Schedule-DRMAAc-0.81
export SGE_ROOT=/var/lib/gridengine
ln -f -s /usr/include/drmaa.h
perl Makefile.PL 
make
make install
popd
rm -rf /tmp/$$

echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/var/www/.grid_request.conf /var/www/.grid_request.conf

#Update grid request
wget -P /tmp http://bioifx.org/gridrequest.tgz
tar -C /usr/local/share/perl/5.10.1 -xvzf /tmp/gridrequest.tgz

#All these changes are now in the tgz
#modify switch.sh for dramma.jar
#modify sge_submitter.sh /opt/workflow-sforge/bin/sge_submitter.sh
#perl -pi -e 's/export SGE_ROOT=.*/export SGE_ROOT=\/var\/lib\/gridengine/' /opt/workflow-sforge/bin/sge_submitter.sh
#perl -pi -e 's/export SGE_ARCH=.*/export SGE_ARCH=lx26-ia64/' /opt/workflow-sforge/bin/sge_submitter.sh
#perl -pi -e 's/opt\/sge/\/\/opt\/workflow-sforge\/jars\/drmaa.jar\:/var\/lib\/gridengine/' /opt/workflow-sforge/switch.sh

#export SGE_CELL=default
#export SGE_QMASTER_PORT=6444
#export SGE_EXECD_PORT=6445



#Workflow, sge user config
#adduser --quiet --disabled-password --disabled-login guest
mkdir -p /home/www-data
chown www-data:www-data /home/www-data
chmod 755 /home/www-data
#in /etc/passwd
perl -pi -e 's/^www-data.*/www-data:x:33:33:www-data:\/home\/www-data:\/bin\/bash/' /etc/passwd
