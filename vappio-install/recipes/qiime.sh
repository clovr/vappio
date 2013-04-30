#!/bin/bash

# Need the developmental headers in place in order to use easy_install
apt-get -y install python-dev

apt-get -y install python-numpy

# Need to install cogent 1.4.1 from SourceForge using easy_install
easy_install "http://sourceforge.net/projects/pycogent/files/PyCogent/1.4.1/PyCogent-1.4.1.tgz/download"

#Qiime proper is pulled in currently via clovr opt-packages recipe
