#!/bin/bash

# base code
apt-get install r-base-core

# Need to install gplots package and RColorBrewer pkg
echo "install.packages(c(\"gplots\", \"RColorBrewer\") , repos=\"http://watson.nci.nih.gov/cran_mirror/\")" | R --save --restore

# done
