#!/bin/bash

svn export --force https://vappio.svn.sourceforge.net/svnroot/vappio/trunk/img-conf/etc/perl /etc/perl

#svn export
#cpan
#instmodsh << . | grep -v "cmd?" | sort > cpan.modules.out
#l
#q
#.

apt-get -y install gcc
apt-get -y install libgd2-xpm-dev
export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1
wget -c -P /tmp http://clovr.svn.sourceforge.net/viewvc/clovr/trunk/packages/cpan.packages
#TODO see if we can skip force
cat /tmp/cpan.packages | grep -v "libxml-perl" | perl -ne 'chomp;split(/\s+/);print "cpan -i \"$_[0]\"\n"' | bash -e
