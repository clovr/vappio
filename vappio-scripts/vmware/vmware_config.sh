# VMware specific configuration settings and environmental variables

shared_dir=/shared
shared_mp=/mnt/shared
postgres_data_dir_mp=/mnt/pg_data
postgres_data_dir=$shared_dir/pg_data
postgres_uid=`id postgres -u`
