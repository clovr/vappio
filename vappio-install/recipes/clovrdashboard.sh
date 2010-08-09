#!/bin/bash

source /root/clovrEnv.sh
updateAllDirs.py --clovr-www
/etc/init.d/apache2 reload
