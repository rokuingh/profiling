import sys, os
import numpy as np
import pandas as pd

runs = sys.argv[1]
runs = int(runs)
procs = [36*2**x for x in range(8)]
timeoutfilename = "moab_timing_results.csv"

for num_run in range(1,runs+1):
    for num_procs in procs:

        resfilename = os.path.join(os.getcwd(), str(num_run), str(num_procs), "ESMF_Profile.summary")
        rftmp = resfilename+".tmp"

        out = open(rftmp,"w")
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

        keep_col = ["Native Mesh Source Create", "Native Mesh Destination Create",
                    # "Native Mesh Regrid Store", "Native Mesh Weight Generation",
                    # "Native Mesh ArraySMMStore", "Native Mesh Regrid",
                    "Native Mesh Regrid Store", "Native Mesh Regrid",
                    "Native Mesh Regrid Release", "Native Mesh Source Destroy",
                    "Native Mesh Destination Destroy",
                    "MOAB Mesh Source Create", "MOAB Mesh Destination Create",
                    # "MOAB Mesh Regrid Store", "MOAB Mesh Weight Generation",
                    # "MOAB Mesh ArraySMMStore", "MOAB Mesh Regrid",
                    "MOAB Mesh Regrid Store", "MOAB Mesh Regrid",
                    "MOAB Mesh Regrid Release", "MOAB Mesh Source Destroy",
                    "MOAB Mesh Destination Destroy",
                    ]
        f_out = f_out[keep_col]

        # write new csv
        if not os.path.isfile(timeoutfilename):
            f_out.to_csv(timeoutfilename)
        else:
            with open(timeoutfilename, 'a') as f:
                f_out.to_csv(f, header=False)

        # remove the temp file
        os.remove(rftmp)

        print (("Processed {}").format(str(num_run)+"/"+str(num_procs)))