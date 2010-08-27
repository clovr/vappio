#!/bin/bash

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
source /root/clovrEnv.sh
updateAllDirs.py --opt-packages --stow --clovr_pipelines 

#Updated rnammer to make path the hmmsearch /usr/bin