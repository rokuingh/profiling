import sys
import numpy as np

num_procs = sys.argv[1]
num_procs = int(num_procs)
procs = [x for x in range(num_procs)]
mem_results = np.array([])
num_val = 10

for proc in procs:
    logname = "PET"+str(proc)+".ESMF_LogFile"
    with open(logname) as f:
        for line in f:
            if "VmRSS" in line:
                junk, mem, junk = line.rsplit(None, 2)
                mem_results = np.append(mem_results, float(mem))

# parse out the memory results
assert(len(mem_results) == 2*num_procs*num_val)

ind = np.arange(0,len(mem_results)-1,2)
mem_results2 = mem_results[ind+1] - mem_results[ind]

assert(len(mem_results2) == num_procs*num_val)
# block = np.arange(0,num_val,1)
# mem_results3 = [mem_results2[x*num_val:x*num_val+num_val] for x in range(num_procs)]

mem_results3 = np.reshape(mem_results2, (num_procs,num_val))
mem_results4 = np.sum(mem_results3, axis=0)

out = open("moab_eval_results_mem.csv","a")
if num_procs == 1:
    out.write("memory, measured in Mb")
    out.write("proc count, src create esmf, dst create esmf, regrid esmf, src destroy esmf, dst destroy esmf, "
          "src create moab, dst create moab, regrid moab, src destroy moab, dst destroy moab\n")
out.write(str(num_procs)+", ")
for mem_out in range(num_val):
    out.write(str(mem_results4[mem_out]/1000)+", ")
out.write("\n")
out.close()