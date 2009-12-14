#!/bin/sh

# Import vappio config
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`)"
vlog "###"


# Prep runtime directories
rm -rf $vappio_runtime
mkdir -p $vappio_runtime
chmod 777 $vappio_runtime
touch $vappio_log
chmod 777 $vappio_log


# This is based on /etc/init.d/ec2-run-user-data from alestic.com images
# http://alestic.com/2009/06/ec2-user-data-scripts

# option for the user_data_script to overwrite the next and last commands
NEXT_CMD=$vappio_scripts/setup_node.sh
LAST_CMD="vlog 'Done with run_user_data.sh'"

vlog "Waiting on $vappio_url_base"

# Wait until networking is up on the EC2 instance.
perl -MIO::Socket::INET -e "
 until(new IO::Socket::INET(\"$vappio_url_base\")){print \"Waiting for network...\n\";sleep 1}
"

vlog "Retrieving user data from $vappio_url_user_data"
#user_data=`curl -f -s $vappio_url_user_data`
user_data_file=$(tempfile --prefix ec2 --suffix .user-data --mode 700)
curl --retry 3 --silent --show-error --fail -o $user_data_file $vappio_url_user_data
if [ ! -s $user_data_file ]; then
  vlog "No user-data available"
elif head -1 $user_data_file | egrep -v '^#!'; then
  vlog "Skipping user-data as it does not begin with #!"
else
  vlog "Running user-data"
  # source-ing this so that any environmental variable set will be preserved
  source $user_data_file 1>> $vappio_log 2>> $vappio_log
  vlog "user-data exit code: $?"
fi
rm -f $user_data_file

vlog "Running NEXT_CMD: $NEXT_CMD"
eval $NEXT_CMD

vlog "Running LAST_CMD: $LAST_CMD"
eval $LAST_CMD
