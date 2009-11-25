#!/bin/sh

adduser -p "vaPPiopassword" -u guest
echo "export BASH_ENV=/home/guest/.bashrc" >> /home/guest/.bashrc
 
