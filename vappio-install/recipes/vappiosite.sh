#!/bin/bash

wget http://cb2.igs.umaryland.edu/clovr_vappio_www.tgz
tar -C / -xvzf clovr_vappio_www.tgz

/etc/apache2/sites-available/vappio-internal
/var/www/vappio-internal/

/etc/init.d/apache2 reload
