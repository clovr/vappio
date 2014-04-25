#!/bin/bash

echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/perl /etc/perl

#svn export
#cpan
#instmodsh << . | grep -v "cmd?" | sort > cpan.modules.out
#l
#q
#.

curl -L http://cpanmin.us | perl - --sudo App::cpanminus
export PERL_CPANM_OPT="--skip-installed --notest --auto-cleanup=0"

# Install version of POD::Simple to avoid bug
cpanm --sudo D/DW/DWHEELER/Pod-Simple-3.20.tar.gz

# Avoid a circular dependency in the new version of DateTime-TimeZone
cpanm --sudo D/DR/DROLSKY/DateTime-TimeZone-1.42.tar.gz

# Inline 0.54 refuses to compile as of recent, use 0.53 instead
cpanm --sudo SISYPHUS/Inline-0.53.tar.gz

apt-get -y install perl-doc
apt-get -y install gcc
apt-get -y install libgd2-xpm-dev
export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1
echo p | svn export --force http://svn.code.sf.net/p/clovr/code/trunk/packages/cpan.packages /tmp/cpan.packages

cpanm --sudo YAML

#Consider using a caching server to speed up installs
#http://search.cpan.org/~jettero/CPAN-CachingProxy-1.4002/

cat /tmp/cpan.packages | grep -v "libxml-perl" | perl -ne 'chomp;split(/\s+/);print "cpanm --sudo \"$_[0]\"\n"' | bash -e

#Some modules fail tests and won't install without force
#cpanm --sudo Grid::Request
cpanm --sudo Text::Editor::Easy
cpanm --sudo JSON::PP       ### used for JSON converts in clovr_comparative ws
cpanm --sudo File::Binary   ### used in tag-is-sff metric
cpanm --sudo Data::Random   ### used in clovr_pangenome pipeline for pangenome_do_analysis component 
