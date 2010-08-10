#!/bin/bash

#set /etc/perl/CPAN/Config.pm
#o conf prerequisites_policy follow

#svn export
#cpan
#instmodsh << . | grep -v "cmd?" | sort > cpan.modules.out
#l
#q
#.

export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1
wget http://clovr.svn.sourceforge.net/viewvc/clovr/trunk/packages/cpan.packages
cat cpan.packages | perl -ne 'chomp;split(/\s+/);print "perl -MCPAN -e \"install $_[0]\"\n"' | sh
