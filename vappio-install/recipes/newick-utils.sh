#!/usr/bin/bash

wget -N -P /opt/opt-packages/ http://cb2.igs.umaryland.edu/newick-utils-1.6.tar.gz
tar -xzvf /opt/opt-packages/newick-utils-1.6.tar.gz -C /opt/opt-packages/
ln -sf /opt/opt-packages/newick-utils-1.6 /opt/newick-utilities
rm /opt/opt-packages/newick-utils-1.6.tar.gz
