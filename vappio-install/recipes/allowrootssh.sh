#!/bin/bash

#Allow root login
perl -pi -e 's/command=".*"\s+//' /root/.ssh/authorized_keys  
/etc/init.d/ssh restart
