#!/bin/bash

# base code
apt-get -y install r-base-core

# Need to install gplots package and RColorBrewer pkg
echo "install.packages(c(\"gplots\", \"RColorBrewer\") , repos=\"http://www.ibiblio.org/pub/languages/R/CRAN\")" | R --save --restore

# done
