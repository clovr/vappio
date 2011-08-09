#!/bin/bash

#apt-get install ia32-libs

wget -P /tmp http://trace.ncbi.nlm.nih.gov/Traces/sra/static/sratoolkit.2.1.2-centos_linux64.tar.gz

#wget -P /tmp  http://trace.ncbi.nlm.nih.gov/Traces/sra/static/sratoolkit.2.1.2-ubuntu32.tar.gz

tar -C /opt/opt-packages/ -xf /tmp/sratoolkit.2.1.2-centos_linux64.tar.gz
#tar -C /opt/opt-packages/ -xf /tmp/sratoolkit.2.1.2-ubuntu32.tar.gz

mv /opt/opt-packages/sratoolkit.2.1.2-centos_linux64 /opt/opt-packages/sratoolkit-2.1.2
#mv /opt/opt-packages/sratoolkit.2.1.2-ubuntu32 /opt/opt-packages/sratoolkit-2.1.2
rm /tmp/sratoolkit.2.1.2-centos_linux64.tar.gz
#rm -r /tmp/sratoolkit.2.1.2-ubuntu32.tar.gz

