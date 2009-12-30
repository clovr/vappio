#!/bin/sh

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"

source $vappio_scripts/nimbus/nimbus_config.sh

# modify vappio_config.sh with the nimbus-specific variables recorded in nimbus_config.sh
#mod_config harvesting_dir $nimbus_harvesting_dir
#mod_config staging_dir $nimbus_staging_dir
# know /var/nimbus-metadata-server-url has to exist
#curl -f -s $vappio_url_user_data
#curl http://128.135.125.124:8081/2008-08-08/user-data
$vappio_scripts/run_user_data.sh
