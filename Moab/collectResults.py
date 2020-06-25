#!/usr/bin/python
# coding: utf-8
#

import sys, os, math, re
import numpy as np
import subprocess
from time import localtime, strftime

def timing(EXECDIR, nprocs, runs, testcase, procs, cheyenne=False):
    try:
        import pandas as pd
    except:
        raise ImportWarning("Pandas not available, cannot collect timing results.")
        exit(0)

    print ("\nCollect timing results (<20 min):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))
    if not cheyenne: procs = [nprocs]

    timeoutfilename = os.path.join(EXECDIR, "mbmesh_"+testcase+"_timing_profile_results.csv")

    for num_run in range(1,runs+1):
        for num_procs in procs:
            if num_procs <= nprocs:

                resfilename = os.path.join(EXECDIR, str(num_procs)+"-"+str(num_run), "ESMF_Profile.summary")
                rftmp = resfilename+".tmp"

                out = open(rftmp,"a")
                with open(resfilename) as f:
                    for line in f:
                        # remove leading whitespace
                        nl = line.lstrip()
                        if str(num_procs) in nl:
                            # split out the method name
                            method, rest = nl.split(str(num_procs),1)
                            # remove all but one space in between words
                            newmethod = " ".join(method.split())
                            nl = newmethod+"    "+str(num_procs)+rest
                        out.write(nl)
                out.close()
       
                f_in = pd.read_csv(rftmp, sep=r"\s{2,}", index_col=False, engine='python')
        
                # delete unwanted columns
                keep_col = []
                keep_col.append("Region")
                keep_col.append("Mean (s)")
                f_out = f_in[keep_col]
        
                # switch columns for rows and reorder
                f_out.set_index("Region", inplace=True)
                f_out = f_out.T
        
                f_out.rename(index={"Mean (s)":str(num_procs)}, inplace=True)
       
                # write new csv
                if not os.path.isfile(timeoutfilename):
                    f_out.to_csv(timeoutfilename)
                else:
                    with open(timeoutfilename, 'a') as f:
                        f_out.to_csv(f, header=False)
        
                # remove the temp file
                os.remove(rftmp)

    return timeoutfilename

def create_output_file(str, EXECDIR, testcase):
    if ("Total allocated space" in str): str = "VmTAS"
    memoutfilename = os.path.join(EXECDIR, "mbmesh_"+testcase+"_"+str+"_profile_results.csv")

    out = None
    if not os.path.isfile(memoutfilename):
        out = open(memoutfilename,"w")
        out.write("memory measured in Mb\n")
    else:
        out = open(memoutfilename,"a")
    
    return out, memoutfilename

def make_table(info, logname):
    """
    'info' is a tuple containing (measurement, msrtag) 
    return 'table': a list containing 4-element tuples (tag, method, measurement, value)
    """
    table = []

    # pull measurements and ids from log file, as to mem_results* lists
    with open(logname) as f:
        for line in f:
            if (info[0] in line):
                # split out the method name
                method, rest = line.split("- MemInfo")
                junk, method =  re.compile("PET\d+").split(method)
                # remove all but one space in between words
                method = " ".join(method.split())
    
                # split out tag (before or after)
                tag = method.split(" ")[0]

                # remove tag from method
                method = method.split(" ", 1)[1]

                # split out the measurement name
                junk, measurement, mem = rest.split(":",2)
                measurement = " ".join(measurement.split())

                # split out the timing result as a string
                mem = mem.split()[0]
    
                # convert bytes to kB
                if "bytes" in measurement:
                    mem = float(mem)/1E6
                elif "KiB" in measurement:
                    mem = float(mem)/976.562
                else:
                    mem = float(mem)/1E3

                # set msrtag to shortened label (second element of tuple from meminfo)
                msrtag = info[1]

                entry = (tag, method, msrtag, float(mem))

                table.append(entry)

    return table

def process_table(table):
    """
    return 'table': a list containing 4-element tuples (tag, method, measurement, value)
    """
    from operator import itemgetter

    halflen = int(len(table)/2)

    # subtract values of "before" measurements from "after"s
    val_list = [ (float(a[:][3]) - float(b[:][3])) for a, b in \
                    zip(np.array(sorted(table, key=lambda tup: (tup[1], tup[0])))[0::2,:], \
                        np.array(sorted(table, key=lambda tup: (tup[1], tup[0])))[1::2,:]) ]

    assert (len(val_list) == halflen)

    # Pop all "before"s
    table = [x for x in table if "after" in x[0]]

    # resort the val_list to original ordering
    val_index = sorted(range(len(table)), key=lambda k: table[k])
    unsorted_val_list = [val_list[i] for i in val_index]

    # set the subtracted values on the remaining part of the list
    nptable = np.array(table)
    nptable[:,3] = unsorted_val_list
    
    return nptable


def memory(EXECDIR, nprocs, runs, testcase, procs, cheyenne=False):
    print ("\nCollect memory results (<20 min):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

    if not cheyenne: procs = [nprocs]

    meminfo = [("VmRSS", "VmRSS"), ("VmHWM", "VmHWM"), ("Total allocated space (bytes)", "VmTAS")]

    rss_file, rssfilename = create_output_file(meminfo[0][0], EXECDIR, testcase)
    hwm_file, hwmfilename = create_output_file(meminfo[1][0], EXECDIR, testcase)
    tas_file, tasfilename = create_output_file(meminfo[2][0], EXECDIR, testcase)

    # iterate sets of runs of different processors numbers from 36 - XXK
    run1 = True
    for num_run in range(1,runs+1):
        # iterate runs of increasing number of processors
        for num_procs in procs:
            if num_procs <= nprocs:
                # initialize an array to hold all memory measurements for all processors
                mem_results_list = []

                # iterate per-processor log files
                for proc in range(num_procs):
                    # build the logname
                    logname = os.path.join(EXECDIR, str(num_procs)+"-"+str(num_run),
                        "PET"+(str(proc).zfill(int(math.ceil(math.log(num_procs,10)))))+
                        ".ESMF_LogFile")

                    # initialize a list of tables to hold all memory measurements for one processor
                    tables = []
                    for info in meminfo:
                        tables.append(make_table(info, logname))
                    
                    # process tables of different memory measurement tuples
                    memory_results = []
                    for z in tables:
                        memory_results.append(process_table(z))

                    mem_results_list.append([x for x in memory_results])

                # mem_results_list should have rss, hwm, tas for each processor
                # mem_results_array[proc,msr,method[tag,method,msr,val]]

                # average memory results over processors
                mem_results_array = np.array(mem_results_list)

                mem_rss = mem_results_array[:,0]
                mem_hwm = mem_results_array[:,1]
                mem_tas = mem_results_array[:,2]

                labels = [x for x in mem_rss[0,:,1]]

                # write labels to file
                if run1:
                    rss_file.write("processor count,"+(','.join(map(str,labels)))+'\n')
                    hwm_file.write("processor count,"+(','.join(map(str,labels)))+'\n')
                    tas_file.write("processor count,"+(','.join(map(str,labels)))+'\n')
                    run1 = False
                
                mem_rss2 = np.array([x for x in mem_rss[:,:,3].astype(np.float)])
                mem_rss = np.sum(mem_rss2,0)/mem_rss2.shape[0]
                rss_file.write(str(num_procs)+", "+(",".join(format(x, "10.3f") for  x in mem_rss))+"\n")

                mem_hwm2 = np.array([x for x in mem_hwm[:,:,3].astype(np.float)])
                mem_hwm = np.sum(mem_hwm2,0)/mem_hwm2.shape[0]
                hwm_file.write(str(num_procs)+", "+(",".join(format(x, "10.3f") for  x in mem_hwm))+"\n")

                mem_tas2 = np.array([x for x in mem_tas[:,:,3].astype(np.float)])
                mem_tas = np.sum(mem_tas2,0)/mem_tas2.shape[0]
                tas_file.write(str(num_procs)+", "+(",".join(format(x, "10.3f") for  x in mem_tas))+"\n")

    rss_file.close()
    hwm_file.close()
    tas_file.close()
    
    return rssfilename
