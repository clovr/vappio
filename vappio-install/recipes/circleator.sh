#!/usr/bin/bash

cpan -i Text::CSV
wget -N -P /opt/opt-packages/ http://cb2.igs.umaryland.edu/circleator-1.0alpha8.tar.gz
tar -xzvf /opt/opt-packages/circleator-1.0alpha8.tar.gz -C /opt/opt-packages/
ln -sf /opt/opt-packages/circleator-1.0alpha8 /opt/opt-packages/circleator
ln -sf /opt/opt-packages/circleator-1.0alpha8 /opt/circleator
rm /opt/opt-packages/circleator-1.0alpha8.tar.gz
