#!/bin/bash

source /root/clovrEnv.sh
updateAllDirs.py --vappio-py-www
/etc/init.d/apache2 reload
