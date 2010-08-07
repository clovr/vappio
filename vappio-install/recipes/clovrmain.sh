#!/bin/bash

export VAPPIO_HOME=/opt
export PYTHONPATH=$PYTHONPATH:$VAPPIO_HOME/vappio-py
updateAllDirs.py --opt-packages --stow
