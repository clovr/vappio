#!/bin/bash

qstat -u '*' | head -n $1 

