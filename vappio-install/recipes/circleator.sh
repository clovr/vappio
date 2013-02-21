#!/usr/bin/bash

wget -N -P /opt/opt-packages/ http://cb2.igs.umaryland.edu/circleator.tgz
tar xzvf /opt/opt-packages/circleator.tgz -C /opt/opt-packages/
rm /opt/opt-packages/circleator.tgz
