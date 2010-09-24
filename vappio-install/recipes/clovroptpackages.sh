#!/bin/bash

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
source /root/clovrEnv.sh
updateAllDirs.py --opt-packages 

