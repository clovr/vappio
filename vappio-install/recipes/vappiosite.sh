#!/bin/bash

source /root/clovrEnv.sh
updateAllDirs.py --vappio-py-www

#Gets vappio-internal
wget http://cb2.igs.umaryland.edu/clovr_vappio_www.tgz
tar -C / -xvzf clovr_vappio_www.tgz

/etc/init.d/apache2 reload
