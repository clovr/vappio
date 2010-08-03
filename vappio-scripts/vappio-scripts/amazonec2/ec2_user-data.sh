#!/bin/sh
#
# Retrieve user data passed to a node at startup
echo `curl -f -s http://169.254.169.254/1.0/user-data`

