#!/bin/bash

VAPPIO_HOME=/opt
VAPPIO_RECIPES=$VAPPIO_HOME/vappio-install/recipes

apt-get -y install libxml2-utils
apt-get -y install libxml-parser-perl
apt-get -y install libgraphviz-perl
apt-get -y install libxml-libxml-perl
apt-get -y install libmldbm-perl

#Need to to automate, is interactive
export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1

# installing a specific version of the module
perl -MCPAN -e 'install "GAAS/URI-1.40.tar.gz"'
# otherwise, just
perl -MCPAN -e 'install MLDBM'
perl -MCPAN -e 'install Tree::DAG_Node'
perl -MCPAN -e 'install XML::Simple'

perl -MCPAN -e 'install Date::Manip'
perl -MCPAN -e 'install XML::Writer'
perl -MCPAN -e 'install CDB_File'
perl -MCPAN -e 'install Class::Struct'
perl -MCPAN -e 'install Config::IniFiles'
perl -MCPAN -e 'install Data::Dumper'
perl -MCPAN -e 'install Date::Manip'
perl -MCPAN -e 'install ExtUtils::MakeMaker'
perl -MCPAN -e 'install File::Mirror'
perl -MCPAN -e 'install HTML::Template'
perl -MCPAN -e 'install IO::Tee'
perl -MCPAN -e 'install Log::Cabin'
perl -MCPAN -e 'install Log::Log4perl'
perl -MCPAN -e 'install Math::Combinatorics'
perl -MCPAN -e 'install PerlIO::gzip'
perl -MCPAN -e 'install XML::RSS'
perl -MCPAN -e 'install XML::Writer'
perl -MCPAN -e 'install "C/CJ/CJFIELDS/BioPerl-1.6.1.tar.gz"'
perl -MCPAN -e 'install Aspect'
perl -MCPAN -e 'install MIME::Lite'
# have had to force in the past
perl -MCPAN -e 'install Benchmark::Timer'
perl -MCPAN -e 'install SVN::Agent'


#set ergatis.ini 
#workflow_root
#global_saved_templates
...
#set software config
#Set software.config
#Set Ergatis/IdGenerator/Config.pm

#Install Ergatis
#TODO replace with build_ergatis

wget https://ergatis.svn.sourceforge.net/svnroot/ergatis/trunk/components/shared/software.config

build_ergatis.pl --install_base=/opt/ergatis --htdocs_area=/var/www/ergatis --tmp_area=/tmp --software_config=./software.config --id_generator=Cloud --log /tmp/ergatis.log 

$VAPPIO_RECIPES/build_nightly.pl

#Update configuration
#wget http://cb2.igs.umaryland.edu/ergatis_config.tgz

#wget http://cb2.igs.umaryland.edu/ergatis_clovr.tgz
#tar -C / -xvzf ergatis_clovr.tgz

#Set website
wget http://cb2.igs.umaryland.edu/clovr_ergatis_www.tgz
tar -C / -xvzf clovr_ergatis_www.tgz