#!/bin/bash

# Need the developmental headers in place in order to use easy_install
apt-get y install python-dev

apt-get -y install python-numpy

# Need to install cogent 1.4.1 from SourceForge using easy_install
easy_install "https://downloads.sourceforge.net/project/pycogent/PyCogent/1.4.1/PyCogent-1.4.1.tgz?r=https%3A%2F%2Fsourceforge.net%2Fprojects%2Fpycogent%2Ffiles%2FPyCogent%2F1.4.1%2FPyCogent-1.4.1.tgz%2Fdownload&ts=1283201038&use_mirror=softlayer"

#Qiime proper is pulled in currently via clovr opt-packages recipe
