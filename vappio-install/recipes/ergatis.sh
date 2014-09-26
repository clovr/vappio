#!/bin/bash

VAPPIO_HOME=/opt
VAPPIO_RECIPES=$VAPPIO_HOME/vappio-install/recipes

apt-get -y install libxml2
apt-get -y install libxml-parser-perl
apt-get -y install libgraphviz-perl
apt-get -y install libxml-libxml-perl
apt-get -y install libmldbm-perl
apt-get -y install libjson-perl
apt-get -y install lib32stdc++6
apt-get -y install libyaml-syck-perl
apt-get -y install bioperl

#Need to to automate, is interactive
export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1

# installing a specific version of the module

cpanm --sudo "GAAS/URI-1.40.tar.gz"
# otherwise, just
cpanm --sudo MLDBM
cpanm --sudo Tree::DAG_Node
cpanm --sudo XML::Simple

#Date::Manip version 6.36 seems to be broken; reverting to 6.34
#cpan -i Date::Manip
#Date::Manip versions aside from 6.36 and 5.x have been removed from CPAN
#cpan -i SBECK/Date-Manip-5.34.tar.gz
#6.34 appears to have disappeared from the internet. Keeping this in-house for now.
wget http://cb2.igs.umaryland.edu/libdate-manip-perl_6.34-1_all.deb
dpkg -i libdate-manip-perl_6.34-1_all.deb

cpanm --sudo XML::Writer
cpanm --sudo CDB_File
cpanm --sudo Class::Struct
#There is a bug in 2.63,2.64 that misparses our config files
#http://search.cpan.org/diff?from=Config-IniFiles-2.63&to=Config-IniFiles-2.62
#This commit http://config-inifiles.svn.sourceforge.net/viewvc/config-inifiles/trunk/config-inifiles/lib/Config/IniFiles.pm?r1=198&r2=200
#old versions don't work correctly either cpan -i "WADG/Config-IniFiles-2.38.tar.gz"
#cpan -i "SHLOMIF/Config-IniFiles-2.62.tar.gz"
#2.62 was removed from CPAN
#cpan -i Config::IniFiles
#Pull from bioifx.org
wget http://bioifx.org/configinifiles.tgz
tar -C / -xvzf configinifiles.tgz
cpanm --sudo Data::Dumper
cpanm --sudo Date::Manip
cpanm --sudo ExtUtils::MakeMaker
cpanm --sudo File::Mirror
cpanm --sudo HTML::Template
cpanm --sudo IO::Tee
cpanm --sudo Log::Cabin
cpanm --sudo Log::Log4perl
cpanm --sudo Math::Combinatorics
cpanm --sudo PerlIO::gzip
cpanm --sudo XML::RSS
cpanm --sudo XML::Writer
#cpanm --sudo "C/CJ/CJFIELDS/BioPerl-1.6.1.tar.gz"
#cpanm --sudo BioPerl
cpanm --sudo Aspect
cpanm --sudo MIME::Lite
# have had to force in the past
cpanm --sudo Benchmark::Timer
cpanm --sudo SVN::Agent
cpanm --sudo CGI::Session
# Can't get Grid::Request to install via cpanm, just using cpan for now
# cpan -fi Grid::Request

#Install software.config
rm -f /tmp/software.config
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/vappio-install/recipes/software.config /tmp/software.config

#Get sourceforge SVN certs because SVN sucks and refuses to let you do this with a command line option
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/root/.subversion /root/.subversion
#Install Ergatis
apt-get -y install g++
printenv
export HOME=/root/
export USER=root
rm -rf /tmp/ergatis_install
mkdir -p /tmp/ergatis_install
chmod 777 /tmp/ergatis_install
sudo -E $VAPPIO_RECIPES/build_ergatis.pl --install_base=/opt/ergatis --htdocs_area=/var/www/ergatis --tmp_area=/tmp/ergatis_install --software_config=/tmp/software.config --id_generator=cloud --log /tmp/ergatis.log 
#Ergatis/IdGenerator/Config.pm should be set

mkdir -p /opt/ergatis/global_id_repository/logs
chmod -R 777 /opt/ergatis/global_id_repository
touch /opt/ergatis/global_id_repository/valid_id_repository

#Install symlink to clovr project_saved_repository
rm -rf /opt/ergatis/global_saved_templates
ln -f -s /opt/clovr_pipelines/workflow/project_saved_templates /opt/ergatis/global_saved_templates

#Configure website
#Pull ergatis.ini, Config.pm
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/vappio-install/recipes/ergatis.ini /var/www/ergatis/cgi/ergatis.ini
chmod a+r /var/www/ergatis/cgi/ergatis.ini
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/vappio-install/recipes/Config.pm /var/www/ergatis/cgi/Ergatis/IdGenerator/Config.pm
chmod a+r /var/www/ergatis/cgi/Ergatis/IdGenerator/Config.pm
echo p | svn export --force  https://svn.code.sf.net/p/vappio/code/trunk/vappio-install/recipes/kill_wf.cgi /var/www/ergatis/cgi/kill_wf.cgi
chmod a+rx /var/www/ergatis/cgi/kill_wf.cgi

#Pull old version of pipeline.pm 
#Latest code changes the environment
echo p | svn export --force -r r7110 https://svn.code.sf.net/p/ergatis/code/trunk/lib/Ergatis/Pipeline.pm /opt/ergatis/lib/perl5/Ergatis/Pipeline.pm



#DEPRECATED
#Update configuration
#wget http://cb2.igs.umaryland.edu/ergatis_config.tgz
#tar -C / -xvzf ergatis_clovr.tgz
#rm -f /tmp/clovr_ergatis_www.tgz
#wget -P /tmp http://cb2.igs.umaryland.edu/clovr_ergatis_www.tgz
#tar -C / -xvzf /tmp/clovr_ergatis_www.tgz

