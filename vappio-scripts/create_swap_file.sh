#!/bin/bash
## Create a swap file for use on EC2
vappio_scripts=/opt/vappio-scripts
source $vappio_scripts/vappio_config.sh

vlog "###"
vlog "### $0 (`whoami`) on `hostname`"
vlog "###"

# Grab the total memory size on this node
total_mem=`cat /proc/meminfo | grep MemTotal | perl -ne '/MemTotal:\s*(\d+)/; print $1;'`

# We want to create a swap space file that is at least the size of our memory.
# But we need to do some math to make sure that the swap file we create is a factor of 2.
SWAP_SIZE_MEGABYTES=$(($total_mem/1024/1024))
SWAP_SIZE_MEGABYTES=$(($SWAP_SIZE_MEGABYTES+1))

if [ $((SWAP_SIZE_MEGABYTES % 2)) != 0 ]; then
    vlog "Memory is not a factor of 2, using default swap file size of 8GB"
    SWAP_SIZE_MEGABYTES=8
fi           

vlog "Creating /swapfile of $SWAP_SIZE_MEGABYTES Megabytes"
dd of=/mnt/.swapfile.1 bs=1 count=0 seek=$(($SWAP_SIZE_MEGABYTES*1024))M 1>>$vappio_log 2>>$vappio_log   
#Make sure loop module is loaded
modprobe loop
#Setup loop back device
losetup /dev/loop0 /mnt/.swapfile.1 
mkswap /dev/loop0 1>>$vappio_log 2>>$vappio_log
swapon /dev/loop0 1>>$vappio_log 2>>$vappio_log
vlog "Swap Status:"    
swapon -s 1>>$vappio_log 2>>$vappio_log
