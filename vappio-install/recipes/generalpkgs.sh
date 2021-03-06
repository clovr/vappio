#!/bin/sh

apt-get -y install screen-profiles

apt-get -y install wget curl apache2 binutils openjdk-6-jre-headless diff dnsutils rsync vim csh tcsh dpkg-dev build-essential libxml2-utils 

apt-get -y install tk8.5 tcl8.5

apt-get -y install libapr1-dev libavalon-framework-java libbatik-java libblas-dev libblas3gf libbsf-java libbsf-java libcairo2-dev 

apt-get -y install libcairo2-dev rhino

apt-get -y install subversion

apt-get -y install libreadline5-dev

apt-get -y install expect

apt-get -y install python-dev

apt-get -y install python-argparse

apt-get -y install python-numpy

#apt-get -y install python-biopython

apt-get -y install lynx

apt-get -y install tofrodos
## Also drop a symlink in /usr/local/bin to dos2unix so older scripts work
ln -s /usr/bin/fromdos /usr/bin/dos2unix

apt-get -y install git-core
