# Nimbus specific configuration settings and environmental variables
export vappio_url_base=`cat /var/nimbus-metadata-server-url | perl -pe 's/http:\/\///'`  # remove http://
export vappio_url_user_data=`cat /var/nimbus-metadata-server-url`/2008-08-08/user-data

nimbus_harvesting_dir=/mnt/harvesting
nimbus_staging_dir=/mnt/staging
