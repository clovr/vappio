#!/bin/bash
wget http://cb2.igs.umaryland.edu/wf_clovr.tgz
tar -C / -xvzf wf_clovr.tgz
#Mod with dcespec/queue support
#wget http://cb2.igs.umaryland.edu/wf_clovr_3.0vp2.tgz
#tar -C / -xvzf wf_clovr_3.0vp2.tgz
chmod 777 /opt/workflow-sforge/idfile
chown www-data:www-data /opt/workflow-sforge/idfile

wget http://cb2.igs.umaryland.edu/drmaa.jar
SGE_ROOT=/var/lib/gridengine
mkdir -p $SGE_ROOT/lib
cp drmaa.jar $SGE_ROOT/lib
cp drmaa.jar /opt/workflow-sforge/jars/
apt-get -y install libdrmaa1.0 libdrmaa-dev

ln -f -s /usr/lib $SGE_ROOT/lib/lx26-ia64

mkdir /tmp/$$
pushd /tmp/$$
wget http://search.cpan.org/CPAN/authors/id/T/TH/THARSCH/Schedule-DRMAAc-0.81.tar.gz
tar xvzf Schedule-DRMAAc-0.81.tar.gz 
cd Schedule-DRMAAc-0.81
export SGE_ROOT=/var/lib/gridengine
ln -f -s /usr/include/drmaa.h
perl Makefile.PL 
make
make install
popd
rm -rf /tmp/$$

svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/var/www/.grid_request.conf /var/www/.grid_request.conf

#Update grid request
wget -P /tmp http://cb2.igs.umaryland.edu/gridrequest.tgz
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
