#!/bin/bash

# base code
apt-get --force-yes -y install r-base
apt-get --force-yes -y install r-base-dev

# Need to install gplots package and RColorBrewer pkg
echo "install.packages(c(\"gplots\", \"RColorBrewer\") , repos=\"http://www.ibiblio.org/pub/languages/R/CRAN\")" | R --save --restore

echo "source(\"http://bioconductor.org/biocLite.R\");
biocLite(\"DESeq\")" | R --save --restore

# done
