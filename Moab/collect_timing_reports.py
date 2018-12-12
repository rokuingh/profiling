import sys, os
import numpy as np

num_procs  = sys.argv[1]
num_procs = int(num_procs)

resfilename = os.path.join(os.getcwd(), str(num_procs), "MOAB_eval"+str(num_procs)+".out")

out = None
timeoutfilename = "moab_timing_results.csv"
if not os.path.isfile(timeoutfilename):
    out = open(timeoutfilename,"w")
    out.write("timing measured in seconds\n")
    out.write("proc count\tsrc create esmf\tdst create esmf\tregrid store esmf\tregrid esmf\tregrid release esmf\tsrc destroy esmf\tdst destroy esmf\tsrc create moab\tdst create moab\tregrid moab\tsrc destroy moab\tdst destroy moab\n")
else:
    out = open(timeoutfilename,"a")

out.write(str(num_procs)+", ")
with open(resfilename) as f:
    for line in f:
        if "time" in line:
            junk, max, avg = line.rsplit(None, 2)
            out.write(str(avg)+"\t")
    out.write("\n")

out.close()
