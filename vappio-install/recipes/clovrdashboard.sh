#!/bin/bash

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
source /opt/vappio-scripts/clovrEnv.sh
updateAllDirs.py --clovr-www
cp -f /var/www/clovr/redirect.html /var/www/index.html
/etc/init.d/apache2 reload
