#!/usr/bin/bash

wget -N -P /opt/opt-packages/ http://cb2.igs.umaryland.edu/batik-1.6.tgz
tar xzvf /opt/opt-packages/batik-1.6.tgz -C /opt/opt-packages/
rm /opt/opt-packages/batik-1.6.tgz
ln -sf /opt/opt-packages/batik-1.6 /opt/batik
