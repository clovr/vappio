# set environmental variables for running on EC2
export vappio_url_base=169.254.169.254:80
export vappio_url_user_data=http://169.254.169.254/latest/user-data

#The staging and harvesting directories must be under
#ec2_localmount
ec2_localmount=/mnt
ec2_staging_dir=$ec2_localmount/staging
ec2_harvesting_dir=$ec2_localmount/harvesting

export JAVA_HOME=/usr/lib/jvm/java-6-openjdk/
#export EC2_HOME=/opt/opt-packages/ec2-api-tools-1.3-24159
#export EC2_AMITOOL_HOME=/opt/opt-packages/ec2-ami-tools-1.3-45758
#export PATH=$PATH:$EC2_HOME/bin
#ec2pkfile=`cat /var/vappio_runtime/ec2pkfile`
#ec2certfile=`cat /var/vappio_runtime/ec2certfile`
#export EC2_PRIVATE_KEY=$ec2pkfile
#export EC2_CERT=$ec2certfile
