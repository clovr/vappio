#!/bin/bash

VAPPIO_HOME=/opt
VAPPIO_RECIPES=$VAPPIO_HOME/vappio-install/recipes

apt-get -y install libxml2
apt-get -y install libxml-parser-perl
apt-get -y install libgraphviz-perl
apt-get -y install libxml-libxml-perl
apt-get -y install libmldbm-perl

#Need to to automate, is interactive
export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1

# installing a specific version of the module

cpan -i "GAAS/URI-1.40.tar.gz"
# otherwise, just
cpan -i MLDBM
cpan -i Tree::DAG_Node
cpan -i XML::Simple

cpan -i Date::Manip
cpan -i XML::Writer
cpan -i CDB_File
cpan -i Class::Struct
cpan -i Config::IniFiles
cpan -i Data::Dumper
cpan -i Date::Manip
cpan -i ExtUtils::MakeMaker
cpan -i File::Mirror
cpan -i HTML::Template
cpan -i IO::Tee
cpan -i Log::Cabin
cpan -i Log::Log4perl
cpan -i Math::Combinatorics
cpan -i PerlIO::gzip
cpan -i XML::RSS
cpan -i XML::Writer
cpan -i "C/CJ/CJFIELDS/BioPerl-1.6.1.tar.gz"
cpan -i Aspect
cpan -i MIME::Lite
# have had to force in the past
cpan -fi Benchmark::Timer
cpan -i SVN::Agent

#Install software.config
rm -f /tmp/software.config
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-install/recipes/software.config /tmp/software.config

#Get sourceforge SVN certs because SVN sucks and refuses to let you do this with a command line option
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/root/.subversion /root/.subversion
#Install Ergatis
apt-get -y install g++
printenv
export HOME=/root/
export USER=root
mkdir -p /tmp/ergatis_install
chmod 777 /tmp/ergatis_install
sudo -E $VAPPIO_RECIPES/build_ergatis.pl --install_base=/opt/ergatis --htdocs_area=/var/www/ergatis --tmp_area=/tmp/ergatis_install --software_config=/tmp/software.config --id_generator=cloud --log /tmp/ergatis.log 
#Ergatis/IdGenerator/Config.pm should be set

mkdir -p /opt/ergatis/global_id_repository/logs
chmod -R 777 /opt/ergatis/global_id_repository
touch /opt/ergatis/global_id_repository/valid_id_repository

#Install symlink to clovr project_saved_repository
rm -rf /opt/ergatis/global_saved_templates
ln -s /opt/clovr_pipelines/workflow/project_saved_templates /opt/ergatis/global_saved_templates

#Configure website
#Pull ergatis.ini, Config.pm
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-install/recipes/ergatis.ini /var/www/ergatis/ergatis.ini
chmod a+r /var/www/ergatis/ergatis.ini
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-install/recipes/Config.pm /var/www/ergatis/cgi/Ergatis/IdGenerator/Config.pm
chmod a+r /var/www/ergatis/cgi/Ergatis/IdGenerator/Config.pm
svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/vappio-install/recipes/kill_wf.cgi /var/www/ergatis/cgi/kill_wf.cgi
chmod a+rx /var/www/ergatis/cgi/kill_wf.cgi
#DEPRECATED
#Update configuration
#wget http://cb2.igs.umaryland.edu/ergatis_config.tgz
#tar -C / -xvzf ergatis_clovr.tgz
#rm -f /tmp/clovr_ergatis_www.tgz
#wget -P /tmp http://cb2.igs.umaryland.edu/clovr_ergatis_www.tgz
#tar -C / -xvzf /tmp/clovr_ergatis_www.tgz

