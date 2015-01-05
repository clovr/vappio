#!/bin/bash -eux

# Add clovr user to sudoers.
echo "clovr        ALL=(ALL)       NOPASSWD: ALL" >> /etc/sudoers
sed -i "s/^.*requiretty/#Defaults requiretty/" /etc/sudoers
