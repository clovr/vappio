#!/bin/bash

#set /etc/perl/CPAN/Config.pm
#o conf prerequisites_policy follow

#svn export
#cpan
#instmodsh << . | grep -v "cmd?" | sort > cpan.modules.out
#l
#q
#.

apt-get -y install gcc
export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1
wget -c -P /tmp http://clovr.svn.sourceforge.net/viewvc/clovr/trunk/packages/cpan.packages
cat /tmp/cpan.packages | grep -v "libxml-perl" | perl -ne 'chomp;split(/\s+/);print "cpan -fi \"$_[0]\"\n"' | bash -e
