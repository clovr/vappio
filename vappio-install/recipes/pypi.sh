#!/bin/bash

## Install pip
## Moved to vappiopkgs so we don't get errors during build process
apt-get -y install python-pip

## Install python modules
apt-get -y install python-biopython
pip install HTSeq
pip install bx-python
