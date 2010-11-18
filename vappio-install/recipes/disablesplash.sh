#!/bin/bash

rename -f 's/plymouth(\S*)\.conf/plymouth$1.conf.disabled/' /etc/init/plymouth*.conf
