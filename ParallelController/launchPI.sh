#!/bin/bash
#$ -N MPITEST
#$ -q free64
#$ -pe one-node-mpi 20
#$ -R y

# Module load OpenMPI
module load openmpi-3.1.2/gcc-6.4.0

which mpicc
mpicxx main.cpp MiniPID.cpp -o hello

# To keep Mellanox mxm from complaining
ulimit -S -s 10240

which mpirun
mpirun -np $CORES  hello  > out

rm -rf MPITEST.o*
rm -rf MPITEST.e*