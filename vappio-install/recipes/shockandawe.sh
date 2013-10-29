#!/bin/bash

DATE=`date +"%Y.%m.%d"`

# git is needed to pull down shockandawe
apt-get -y install git-core

#######################
# postgresql
#######################
apt-get -y install postgresql-8.4
apt-get -y install postgresql-contrib-8.4

# Because we want to have a password-less login we have to export a custom
# postgres pg_hba.conf file and restart postgres
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/etc/postgresql/8.4/main/pg_hba.conf /etc/postgresql/8.4/main/pg_hba.conf
/etc/init.d/postgresql-8.4 restart

# Create our user and database
sudo -u postgres createuser -h localhost -S -d -R clovr
sudo -u postgres createdb -h localhost awe
sudo -u postgres createlang -h localhost plpgsql awe

#######################
# nodejs
#######################
mkdir -p /tmp/nodejs
mkdir -p /opt/opt-packages/nodejs-4.0
wget -P /tmp/nodejs/ http://nodejs.org/dist/node-v0.4.0.tar.gz
tar xfv /tmp/nodejs/node-v0.4.0.tar.gz -C /tmp/nodejs/

cd /tmp/nodejs/node-v0.4.0/
configure --prefix=/opt/opt-packages/nodejs-4.0
make
make install

# Add nodejs to our PATH and setup our NODE_PATH
export PATH=$PATH:/opt/opt-packages/nodejs-4.0/bin
export NODE_PATH=/opt/opt-packages/npm-${DATE}/

#######################
# npm
#######################
mkdir -p /opt/opt-packages/npm-${DATE}
mkdir -p /opt/opt-packages/npm-${DATE}/bin
mkdir -p /opt/opt-packages/npm-${DATE}/man

# In order to install npm to a custom directory we need to write out our 
# .npmrc designated where we should install things
cat > /root/.npmrc <<EOF
root=/opt/opt-packages/npm-${DATE}
binroot=/opt/opt-packages/npm-${DATE}/bin
manroot=/opt/opt-packages/npm-${DATE}/man
EOF

cd /tmp

# Now install npm
curl http://npmjs.org/install.sh | sh

# ...and the npm libraries shockandawe needs
/opt/opt-packages/npm-${DATE}/bin/npm install express formidable pg jade

#######################
# shockandawe
#######################
apt-get -y install python-biopython
apt-get -y install python-psycopg2

git clone git://git.mcs.anl.gov/shockandawe.git /opt/opt-packages/shockandawe-${DATE}

# Load the AWE scheme into our postgres server
psql -h localhost -U clovr awe < /opt/opt-packages/shockandawe-${DATE}/AWE/AWEBackend.sql

# Some of the config files that shockandawe uses must be pulled down froms svn
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/opt/opt-packages/shockandawe/AWE/conf.json /opt/opt-packages/shockandawe-${DATE}/AWE/conf.json
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/opt/opt-packages/shockandawe/AWEClient/AWE.conf /opt/opt-packages/shockandawe-${DATE}/AWEClient/AWE.conf
echo p | svn export --force https://svn.code.sf.net/p/vappio/code/trunk/img-conf/opt/opt-packages/shockandawe/Shock/conf.json /opt/opt-packages/shockandawe-${DATE}/Shock/conf.json

# Clean everything up once we are done
rm -rf /tmp/nodejs
