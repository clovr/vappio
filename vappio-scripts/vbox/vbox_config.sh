# VirtualBox specific configuration settings and environmental variables

shared_dir=shared
shared_mp=/mnt
userdata_dir=user_data
userdata_mp=/mnt/user_data
keys_dir=/mnt/keys
postgres_data_dir_mp=/mnt/pg_data
#Unlike vmware, vbox is not letting us nest this mount
#postgres_data_dir=$shared_dir/pg_data
postgres_data_dir=pg_data
postgres_uid=`id postgres -u`
postgres_data_dir_tarball=/opt/pg_data.tgz
