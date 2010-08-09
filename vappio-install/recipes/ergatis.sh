#!/bin/bash
apt-get -y install libxml2-utils
apt-get -y install libxml-parser-perl
apt-get -y install libgraphviz-perl
apt-get -y install libxml-libxml-perl
apt-get -y install libmldbm-perl
# install modules normally
#Need to to automate, is interactive
perl -MCPAN -e shell
# installing a specific version of the module
install GAAS/URI-1.40.tar.gz
# otherwise, just
install Date::Manip 
install XML::Writer
install CDB_File
install Class::Struct
install Config::IniFiles
install Data::Dumper
install Date::Manip
install ExtUtils::MakeMaker
install File::Mirror
install HTML::Template
install IO::Tee
install Log::Cabin
install Log::Log4perl
install Math::Combinatorics
install PerlIO::gzip
install XML::RSS
install XML::Writer
install C/CJ/CJFIELDS/BioPerl-1.6.1.tar.gz
install Aspect
install MIME::Lite
# have had to force in the past
install Benchmark::Timer 

#set ergatis.ini 
#workflow_root
#global_saved_templates
...
#set software config
#Set software.config
#Set Ergatis/IdGenerator/Config.pm

#Install Ergatis


#Update configuration
wget http://cb2.igs.umaryland.edu/ergatis_config.tgz

#wget http://cb2.igs.umaryland.edu/ergatis_clovr.tgz
#tar -C / -xvzf ergatis_clovr.tgz

wget http://cb2.igs.umaryland.edu/clovr_ergatis_www.tgz
tar -C / -xvzf clovr_ergatis_www.tgz