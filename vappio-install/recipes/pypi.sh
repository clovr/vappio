#!/bin/bash

## Install pip
## Moved to vappiopkgs so we don't get errors during build process
#apt-get -y install python-pip

## Install python modules
pip install HTSeq
pip install biopython
pip install bx-python
