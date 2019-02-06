#!/bin/bash

qsub array_dram_w.sh
qsub array_dram.sh
qsub array_l2_w.sh
qsub array_l2.sh
qsub array_l1d_w.sh
qsub array.sh