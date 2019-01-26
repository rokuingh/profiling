import sys, os, re
import numpy as np
import math

runs = sys.argv[1]
runs = int(runs)

procs = [36*2**x for x in range(8)]

out = None
memoutfilename = "moab_memory_results.csv"

if not os.path.isfile(memoutfilename):
    out = open(memoutfilename,"w")
    out.write("memory measured in Mb\n")
    # out.write("proc count\tsrc create hwm esmf\tsrc create rss esmf\tdst create hwm esmf\tdst create rss esmf\tregrid store hwm esmf\tregrid store rss esmf\tregrid hwm esmf\tregrid rss esmf\tregrid release hwm esmf\tregrid release rss esmf\tsrc destroy hwm esmf\tsrc destroy rss esmf\tdst destroy hwm esmf\tdst destroy rss esmf\tsrc create hwm moab\tsrc create rss moab\tdst create hwm moab\tdst create rss moab\tregrid store hwm moab\tregrid store rss moab\tregrid hwm moab\tregrid rss moab\tregrid release hwm moab\tregrid release rss moab\tsrc destroy hwm moab\tsrc destroy rss moab\tdst destroy hwm moab\tdst destroy rss moab\n")
else:
    out = open(memoutfilename,"a")


num_val = 18
num_measurements = 2
meminfo = ["VmRSS", "Total allocated space (bytes)"]

# iterate sets of runs of different processors numbers from 36 - XXK
run1 = True
for num_run in range(1,runs+1):
    # iterate runs of increasing number of processors
    for num_procs in procs:
        # initialize an array to hold all memory measurements for all processors
        mem_results_array = np.zeros([num_procs, num_val*num_measurements])
        # init list for labels
        labels = []
        # iterate per-processor log files
        for proc in range(num_procs):
            # initialize an array to hold all memory measurements for one processor
            mem_results = []
            # build the logname
            logname = os.path.join(os.getcwd(), str(num_run), str(num_procs),
                "PET"+(str(proc).zfill(int(math.ceil(math.log(num_procs,10)))))+
                ".ESMF_LogFile")
            with open(logname) as f:
                for line in f:
                    if any(x in line for x in meminfo):
                        # split out the method name
                        method, rest = line.split("- MemInfo")
                        junk, method = re.compile("PET\d+").split(method)
                        # remove all but one space in between words
                        method = " ".join(method.split())

                        # split out the measurement name
                        junk, msr, time = rest.split(":",2)
                        msr = " ".join(msr.split())

                        # split out the timing result as a string
                        time = time.split()[0]

                        # convert bytes to kB
                        if "bytes" in msr:
                            time = float(time)/1E3
                        else:
                            time = float(time)/1E6

                        mem_results.append((method+" "+msr, float(time)))

            # sort memory results, and subtract before from after
            mem_results.sort(key=lambda tup: tup[0])
            mem_results = [ (b[0], a[1] - b[1]) for a, b in \
                             zip(mem_results[0:num_val*num_measurements], \
                                 mem_results[num_val*num_measurements: \
                                             2*num_val*num_measurements]) ]

            # split tuples into times and labels, split off 'before' from labels
            mems =  [x[1] for x in mem_results]
            # split off the 'before' and '(bytes)' from labels
            labels = [x[0].split("before ")[1] for x in mem_results]
            labels = [x.split(" (bytes)")[0] if "bytes" in x else x for x in labels]

            # write mem results to numpy array
            assert(len(mems) == (num_val*num_measurements))
            mem_results_array[proc,:] = np.array(mems)

        # average memory results over processors
        mem = np.sum(mem_results_array,0)/mem_results_array.shape[0]

        # write labels to file
        if run1:
            out.write("processor count, "+(','.join(map(str,labels)))+'\n')
            run1 = False
        out.write(str(num_procs)+", "+(",".join(format(x, "10.3f") for x in mems))+"\n")

out.close()
