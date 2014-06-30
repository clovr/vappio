# VMware specific configuration settings and environmental variables

shared_dir=/shared
shared_mp=/mnt
userdata_dir=/user_data
userdata_mp=/mnt/user_data
keysdir=/mnt/keys
vappioconf_dir=/vappio-conf
vappioconf_mp=/mnt/vappio-conf
postgres_data_dir_mp=/mnt/pg_data
postgres_data_dir=$shared_dir/pg_data
postgres_uid=`id postgres -u`
postgres_guid=`id postgres -g`
postgres_data_dir_tarball=/opt/pg_data.tgz
