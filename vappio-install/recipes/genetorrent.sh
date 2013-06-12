#!/usr/bin/bash

wget -N -P /opt/opt-packages/ http://cb2.igs.umaryland.edu/genetorrent-3.8.3.tgz
tar -xzvf /opt/opt-packages/genetorrent-3.8.3.tgz -C /opt/opt-packages/
ln -sf /opt/opt-packages/genetorrent-3.8.3 /opt/genetorrent
rm /opt/opt-packages/genetorrent-3.8.3.tgz
