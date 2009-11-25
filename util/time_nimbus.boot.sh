#!/bin/bash
# time_nimbus_boot.sh <image> <hours>
# record image boot times to a file
LOGFILE=time_nimbus_boot.out
IMAGE=$1
HOURS=$2
TIMESTAMP=`date`
CMD="/export/prog/nimbus-cloud-client-013/bin/cloud-client.sh --run --name $IMAGE --hours $HOURS"

#CMD="sleep 2"

#echo [$IMAGE] >> time_test.out

/usr/bin/time -o $LOGFILE -a -f "$TIMESTAMP\t$IMAGE\t%e" $CMD
