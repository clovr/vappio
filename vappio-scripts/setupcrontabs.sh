#!/bin/bash

# Import vappio config
source /root/clovrEnv.sh
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

##
# Setup crontabs
crontab -u root $VAPPIO_HOME/vappio-scripts/crontab.conf
