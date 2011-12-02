#!/bin/bash

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
source /opt/vappio-scripts/clovrEnv.sh
updateAllDirs.py --clovr-www

# Put the redirect html in place
mv -f /var/www/index.html /var/www/index.html_preclovr
cp /var/www/clovr/redirect.html /var/www/index.html
cp /var/www/clovr/favicon.ico /var/www/favicon.ico
/etc/init.d/apache2 reload
