import sys, os
import numpy as np
import math

num_procs  = sys.argv[1]
num_procs = int(num_procs)

out = None
memoutfilename = "moab_memory_results.csv"
if not os.path.isfile(memoutfilename):
    out = open(memoutfilename,"w")
    out.write("memory measured in Mb\n")
    out.write("proc count\tsrc create hwm esmf\tsrc create rss esmf\tdst create hwm esmf\tdst create rss esmf\tregrid hwm esmf\tregrid rss esmf\tsrc destroy hwm esmf\tsrc destroy rss esmf\tdst destroy hwm esmf\tdst destroy rss esmf\tsrc create hwm moab\tsrc create rss moab\tdst create hwm moab\tdst create rss moab\tregrid hwm moab\tregrid rss moab\tsrc destroy hwm moab\tsrc destroy rss moab\tdst destroy hwm moab\tdst destroy rss moab\n")
else:
    out = open(memoutfilename,"a")


procs = [x for x in range(num_procs)]
mem_results = []
num_val = 10
num_measurements = 2

for proc in procs:
    logname = os.path.join(os.getcwd(), str(num_procs),
        "PET"+(str(proc).zfill(int(math.ceil(math.log(num_procs,10)))))+
        ".ESMF_LogFile")
    with open(logname) as f:
        for line in f:
            if "VmRSS" in line:
                junk, rss, junk = line.rsplit(None, 2)
                mem_results.append(float(rss))
            elif "VmHWM" in line:
                junk, hwm, junk = line.rsplit(None, 2)
                mem_results.append(float(hwm))

# parse out the memory results
mem_results = np.array(mem_results)
assert(len(mem_results) == (2*num_procs*num_val*num_measurements))

# separate rss and hwm numbers into columns, hwm first
ind = np.arange(0,len(mem_results)-1,2)
mem_results2 = np.empty((2*num_procs*num_val, num_measurements))
mem_results2[:,0] = mem_results[ind]
mem_results2[:,1] = mem_results[ind+1]

# now subtract the 'after' from the 'before' measurements
ind = np.arange(0,mem_results2.shape[0]-1,2)
mem_results3 = mem_results2[ind+1,:] - mem_results2[ind,:]

assert(mem_results3.shape == (num_procs*num_val, 2))

mem_results4 = np.reshape(mem_results3, (num_procs,num_val,num_measurements))
mem_results5 = np.sum(mem_results4, axis=0)

out.write(str(num_procs)+"\t")
for mem_out in range(num_val):
    out.write(str(mem_results5[mem_out,0]/1000)+"\t")
    out.write(str(mem_results5[mem_out,1]/1000)+"\t")
out.write("\n")

out.close()
