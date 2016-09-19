import sys
import numpy as np

num_power = sys.argv[1]
num_power = int(num_power)

procs = [2**x for x in range(num_power)]

filename = "MOAB_eval"

out = open("moab_eval_results.csv","w")
out.write("proc count, src create esmf, dst create esmf, regrid esmf, src destroy esmf, dst destroy esmf, "
          "src create moab, dst create moab, regrid moab, src destroy moab, dst destroy moab\n")


for np in procs:
    out.write(str(np)+", ")
    with open(filename+str(np)+".out") as f:
        for line in f:
            if "time" in line:
                junk, max, avg = line.rsplit(None, 2)
                out.write(str(avg)+", ")
        out.write("\n")

out.close()