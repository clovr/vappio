#!/bin/bash

source /opt/vappio-scripts/clovrEnv.sh
updateAllDirs.py --vappio-py-www

#Gets vappio-internal
wget http://bioifx.org/clovr_vappio_www.tgz
tar -C / -xvzf clovr_vappio_www.tgz
ln -fs /etc/apache2/sites-available/vappio-internal /etc/apache2/sites-enabled/vappio-internal

/etc/init.d/apache2 reload
