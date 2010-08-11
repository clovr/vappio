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
cpan -i Benchmark::Timer
cpan -i SVN::Agent


#set ergatis.ini 
#workflow_root
#global_saved_templates

#set software config
#Set software.config
#Set Ergatis/IdGenerator/Config.pm

#Install Ergatis
#TODO replace with build_ergatis

wget -C /tmp https://ergatis.svn.sourceforge.net/svnroot/ergatis/trunk/components/shared/software.config

$VAPPIO_RECIPES/build_ergatis.pl --install_base=/opt/ergatis --htdocs_area=/var/www/ergatis --tmp_area=/tmp --software_config=/tmp/software.config --id_generator=Cloud --log /tmp/ergatis.log 

#Update configuration
#wget http://cb2.igs.umaryland.edu/ergatis_config.tgz

#wget http://cb2.igs.umaryland.edu/ergatis_clovr.tgz
#tar -C / -xvzf ergatis_clovr.tgz

#Set website
wget http://cb2.igs.umaryland.edu/clovr_ergatis_www.tgz
tar -C / -xvzf clovr_ergatis_www.tgz