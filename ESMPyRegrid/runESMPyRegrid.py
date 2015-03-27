#!/usr/bin/python
import os
#
#BSUB -W 00:10
#BSUB -q regular
#BSUB -n 12
#BSUB -J ESMPyRegrid.py
#BSUB -P P35071400
#BSUB -oo ESMPyRegrid.out

os.system("mpirun.lsf python regrid.py")