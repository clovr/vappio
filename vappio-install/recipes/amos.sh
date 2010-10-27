#!/bin/bash

## Need to create symlinks of the AMOS perl modules to /etc/perl so that Ergatis can find them
ln -f -s /opt/opt-packages/bioinf-v1r4b1/AMOS/lib/AMOS /etc/perl/
ln -f -s /opt/opt-packages/bioinf-v1r4b1/AMOS/lib/TIGR /etc/perl/

