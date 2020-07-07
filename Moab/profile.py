#!/usr/bin/python
# coding: utf-8
#
#
# Ryan O'Kuinghttons
# July 1, 2020
# profile.py
# Usage: python profile.py -np <num_cores> -runs <num_runs> -testcase  <testcase|[create,dual,grid2mesh,redist,regrid-bilinear,regrid-conservative,rendezvous]> --esmfmkfile=<ESMFMKFILE> --execdir=<EXECDIR>
#
import sys, os
import numpy as np
import argparse
import subprocess
from time import localtime, strftime, time


# class Workflow():
#     from collections import namedtuple
#     import itertools
# 
#     def __init__(self, *args, **kwds):
#         self.configurations = configurations
#         # self.configurations = dict(
#         #     np=[4608],
#         #     runs=[10],
#         #     testcase=[create, dual, grid2mesh, redist, regrid, renezvous],
#         # )
# 
#         # testcases = self.iter_product_keywords(keywords)
#         # fail = []
#         # for a in testcases:
#         #     try:
#         #         grid = Grid(np.array([12, 12]),
#         #                     pole_kind=np.array(a.pole_kind),
#         #                     num_peri_dims=a.periodic[0],
#         #                     periodic_dim=a.periodic[1],
#         #                     pole_dim=a.periodic[2],
#         #                     coord_sys=a.coord_sys,
#         #                     coord_typekind=a.typekind,
#         #                     staggerloc=a.staggerloc)
#         #         grid.add_item(GridItem.MASK)
#         #         grid.add_item(GridItem.AREA)
#         #         grid2 = grid[2:10, 4:7]
#         #         self.examine_grid_attributes(grid)
#         #         self.examine_grid_attributes(grid2)
#         #         grid.destroy()
#         #         grid2.destroy()
#         #     except:
#         #         fail += a
# 
#     if len(fail) > 0:
#         raise ValueError(
#             "The following combinations of Grid parameters failed to create a proper Grid: " + str(fail))
# 
# 
# 
#     def itr_row(key, sequence):
#         for element in sequence:
#             yield ({key: element})
# 
#     def iter_product_keywords(keywords, as_namedtuple=True):
#         if as_namedtuple:
#             yld_tuple = namedtuple('ITesterKeywords', keywords.keys())
# 
#         iterators = [itr_row(ki, vi) for ki, vi in keywords.items()]
#         for dictionaries in itertools.product(*iterators):
#             yld = {}
#             for dictionary in dictionaries:
#                 yld.update(dictionary)
#             if as_namedtuple:
#                 yld = yld_tuple(**yld)
#             yield yld
# 
#     def submit_batch_job(self, cmd):
#         p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#         O = ''
#         E = ''
#         last = time()
#         while p.poll() is None:
#             if time() - last > 5:
#                 print('Process is still running')
#                 last = time()
#             tmp = p.stdout.read(1)
#             if tmp:
#                 O += tmp
#             tmp = p.stderr.read(1)
#             if tmp:
#                 E += tmp
#         ret = p.poll(), O+p.stdout.read(), E+p.stderr.read() # Catch remaining output
#         p.stdout.close() # Always close your file handles, or your OS might be pissed
#         p.stderr.close()
#         return ret

def parseArguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Positional mandatory arguments
    parser.add_argument("-np", type=int, help="Number of processing cores")
    parser.add_argument("-runs", type=int, help="Number of runs")
    parser.add_argument("-testcase", type=str, help="Test case  [create,dual,grid2mesh,redist,regrid-bilinear,regrid-conservative,rendezvous]")

    # Optional arguments
    parser.add_argument("--esmfmkfile", type=str, default="", help="Path to esmf.mk, will build ESMF if not supplied.")
    parser.add_argument("--cheyenne", type=str, default="", help="Set to 'on' to use cheyenne specific environment.")
    parser.add_argument("--execdir", type=str, default="", help="Set EXECDIR manually for debugging.")

    # Print version
    parser.add_argument("--version", action="version", version='%(prog)s - Version  0.1')

    # Parse arguments
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    # Parse the arguments
    args = parseArguments()

    # Raw print arguments
    print("\nRunning 'profile.py' with following input parameter values: ")
    for a in args.__dict__:
        print(str(a) + ": " + str(args.__dict__[a]))

    if (args.__dict__["np"] == None):
      raise KeyError("Then number of processors must be specified. Usage: 'python profile.py -np <NP> -runs <RUNS> -testcase <TESTCASE [create,dual,grid2mesh,redist,regrid-bilinear,regrid-conservative,rendezvous] --esmfmkfile <ESMFMKFILE> --cheyenne <None|ON>'")
    elif (args.__dict__["runs"] == None):
      raise KeyError("Then number of runs must be specified. Usage: 'python profile.py -np <NP> -runs <RUNS> -testcase <TESTCASE [create,dual,grid2mesh,redist,regrid-bilinear,regrid-conservative,rendezvous] --esmfmkfile <ESMFMKFILE> --cheyenne <None|ON>'")
    elif (args.__dict__["testcase"] == None):
      raise KeyError("Then testcase must be specified. Usage: 'python profile.py -np <NP> -runs <RUNS> -testcase <TESTCASE [create,dual,grid2mesh,redist,regrid-bilinear,regrid-conservative,rendezvous] --esmfmkfile <ESMFMKFILE> --cheyenne <None|ON>'")

    np = args.__dict__["np"]
    runs = args.__dict__["runs"]
    testcase = args.__dict__["testcase"]
    esmfmkfile = args.__dict__["esmfmkfile"]
    cheyenne = True
    if (args.__dict__["cheyenne"] == ""): cheyenne = False

    debug = True
    if (args.__dict__["execdir"] == ""): debug = False
    else: EXECDIR = args.__dict__["execdir"]

    # Parameters
    ESMFDIR="/glade/work/rokuingh/sandbox/esmf"
    RUNDIR="/glade/work/rokuingh/MBMeshPerformanceResults"
    SRCDIR="/glade/work/rokuingh/sandbox/profiling/Moab"

    GRID1=os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc")
    GRID2=os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc")
    if testcase == "create":
        GRID1=os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.esmf.nc")
        GRID2=os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.esmf.nc")
    if testcase == "dual":
        #GRID1=os.path.join(SRCDIR,"data", "ll1x2e2deg10e6node.esmf.nc")
        #GRID2=os.path.join(SRCDIR,"data", "ll1x2e2deg10e6node.esmf.nc")
        GRID1=os.path.join(SRCDIR,"data", "ll1x2e0deg10e4node.esmf.nc")
        GRID2=os.path.join(SRCDIR,"data", "ll1x2e0deg10e4node.esmf.nc")
    if testcase == "grid2mesh":
        GRID1=os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.scrip.nc")
        GRID2=os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.scrip.nc")

    if not cheyenne:
        ESMFDIR="/home/ryan/Dropbox/sandbox/esmf"
        RUNDIR="/home/ryan/MBMeshPerformanceResults"
        SRCDIR="/home/ryan/Dropbox/sandbox/profiling/Moab"

        GRID1=os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")
        GRID2=os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")
        if testcase == "create":
            GRID1=os.path.join(SRCDIR,"data", "ll1deg.esmf.nc")
            GRID2=os.path.join(SRCDIR,"data", "ll1deg.esmf.nc")
        if testcase == "dual":
            GRID1=os.path.join(SRCDIR,"data", "ll4deg.esmf.nc")
            GRID2=os.path.join(SRCDIR,"data", "ll4deg.esmf.nc")
        if testcase == "grid2mesh":
            GRID1=os.path.join(SRCDIR,"data", "ll1deg.scrip.nc")
            GRID2=os.path.join(SRCDIR,"data", "ll1deg.scrip.nc")


    procs=(36, 72, 144, 288, 576, 1152, 2304, 4608)

    # 1 initialize: build and install esmf and tests with appropriate env vars
    try:
        import initTest
        if not debug: ESMFMKFILE = initTest.build_esmf(ESMFDIR, RUNDIR, SRCDIR, testcase, esmfmkfile=esmfmkfile, cheyenne=cheyenne)
        if not debug: initTest.build_test(ESMFMKFILE, RUNDIR, SRCDIR, testcase, cheyenne=cheyenne)
    except:
        raise RuntimeError("Error building the tests.")

    # 2 run: submit the test runs
    try:
        import runTest
        if not debug: EXECDIR = runTest.setup(SRCDIR, RUNDIR, np, runs, testcase, procs, GRID1, GRID2, cheyenne=cheyenne)
        if not debug: runTest.run(procs, np, SRCDIR, EXECDIR, cheyenne=cheyenne)
    except:
        raise RuntimeError("Error submitting the tests.")

    # 3 post: collect the results into csv files
    if sys.version_info < (3, 5):
        raise EnvironmentError ("Sorry, Python 3.5 or higher is required for test result collection.")

    try:
        import collectResults
        timingfile = collectResults.timing(EXECDIR, np, runs, testcase, procs, cheyenne=cheyenne)
        memoryfile = collectResults.memory(EXECDIR, np, runs, testcase, procs, cheyenne=cheyenne)

        print ("Results are in the following files:\n", timingfile, "\n", memoryfile)
    except:
        raise RuntimeError("Error collecting the test results.")

# !! separate memory files into blocks for rss, hwm, tas

# # 4 report: manual, scp, copy and paste the files into drive spreadsheet and make the appropriate graphs
# 
# # scp rokuingh@cheyenne.ucar.edu:/glade/work/rokuingh/MBMeshPerformanceResults/runs/<num>/mbmesh_$testcase_timing_profile_results.csv .
# # more mbmesh_$testcase_timing_profile_results.csv | xclip -sel clip
# # scp rokuingh@cheyenne.ucar.edu:/glade/work/rokuingh/MBMeshPerformanceResults/runs/<num>/mbmesh_$testcase_memory_profile_results.csv .
# # more mbmesh_$testcase_memory_profile_results.csv | xclip -sel clip
