#!/bin/bash
#$ -N SingleImageTest
#$ -q free128
#$ -m beas

python /data/users/maityb/Modified/PID/video.py 0.0001 >/dev/null 2>&1