#Look for output in /root
#.o and .e files should be zero length

qsub -q wf.q -b y sleep 10
qsub -q exec.q -b y sleep 10
qsub -q repository.q -b y sleep 10
qsub -q staging.q -b y sleep 10
qsub -q stagingsub.q -b y sleep 10
qsub -q harvesting.q -b y sleep 10