#!/bin/bash

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
source /root/clovrEnv.sh
updateAllDirs.py --clovr-www
/etc/init.d/apache2 reload
