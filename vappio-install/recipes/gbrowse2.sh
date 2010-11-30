#!/bin/bash

## Recipe to install gbrowse2
##

export PERL_MM_USE_DEFAULT=1
export PERL_AUTOINSTALL=1

# Install pre-requisites
cpan -fi Bio::Graphics
cpan -fi Capture::Tiny
cpan -fi CGI::Session
cpan -fi Safe::World
cpan -fi DB_File::Lock
cpan -fi File::NFSLock
cpan -fi Bio::DB::Sam

# Download gbrowse2 to a temporary directory in prep for installation
mkdir -p /tmp/gbrowse2_install
wget --tries 20 --retry-connrefused -c -O /tmp/gbrowse2_install/GBrowse-2.03.tar.gz "https://downloads.sourceforge.net/project/gmod/Generic%20Genome%20Browser/GBrowse-2.03/GBrowse-2.03.tar.gz?r=&ts=1288987267&use_mirror=softlayer"
tar xvf /tmp/gbrowse2_install/GBrowse-2.03.tar.gz -C /tmp/gbrowse2_install/

# Start the install process
cd /tmp/gbrowse2_install/GBrowse-2.03/
perl /tmp/gbrowse2_install/GBrowse-2.03/Build.PL --conf=/opt/gbrowse2-2.03 \
                                                 --cgibin=/var/www/gbrowse2/cgi \
                                                 --htdocs=/var/www/gbrowse2/htdocs \
                                                 --databases=/var/www/gbrowse2/databases \
                                                 --tmp=/tmp/gbrowse2 \
                                                 --portdemo=8000 \
                                                 --wwwuser=www-data \
                                                 --apachemodules=/usr/lib/apache2/modules/ 

apt-get --force-yes -y install expect
## We need an expect script here to handle the (stupid) final questions that
## gbrowse's installer will ask
/usr/bin/expect - << EndMark
    exp_internal 1
    spawn /tmp/gbrowse2_install/GBrowse-2.03/Build install

    expect "Do you wish to*"
    send "n\r"
	
    expect "Press any key to continue*"
    send "y\r\n"

    expect eof
EndMark

# Create a sym link to the /opt/gbrowse2 folder 
ln -f -s /opt/gbrowse2-2.03 /opt/gbrowse2

# Need to open up our permissions here to allow www-data to create and modify files
# so that the ergatis component won't fail
chmod -R 777 /opt/gbrowse2-2.03

# Clean up all directories
rm -rf /tmp/gbrowse2_install/
