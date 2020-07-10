#!/usr/bin/python
# coding: utf-8
#
#
# Ryan O'Kuinghttons
# July 1, 2020
# profile.py

import sys, os
import numpy as np
import argparse
import subprocess
from time import localtime, strftime, time

def parseArguments():
    # Create argument parser
    parser = argparse.ArgumentParser()

    # Positional mandatory arguments
    parser.add_argument("-np", type=int, help="Number of processing cores")
    parser.add_argument("-testcase", type=str, help="Test case  [create,dual,grid2mesh,redist,regrid-bilinear,regrid-conservative,rendezvous]")

    # Optional arguments
    parser.add_argument("--branch", type=str, default="mbmesh-redist", help="Branch of the ESMF repo to use.")
    parser.add_argument("--esmfmkfile", type=str, default="", help="Path to esmf.mk, will build ESMF if not supplied.")
    parser.add_argument("--platform", type=str, default="Darwin", help="Set to 'Cheyenne', 'Darwin' or 'Linux'.")
    parser.add_argument("--runs", type=int, default=1, help="Number of runs")

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
      raise KeyError("Then number of processors must be specified. Usage: 'python profile.py -np <NP> -testcase <TESTCASE [create, dual, grid2mesh, redist, regrid-bilinear, regrid-conservative, rendezvous] --branch <BRANCH [default=mbmesh-redist]> --esmfmkfile <ESMFMKFILE> --platform <PLATFORM [Darwin(default), Linux, Cheyenne]> --runs <RUNS [default=1]'")
    elif (args.__dict__["testcase"] == None):
      raise KeyError("Then testcase must be specified. Usage: 'python profile.py -np <NP> -testcase <TESTCASE [create, dual, grid2mesh, redist, regrid-bilinear, regrid-conservative, rendezvous] --branch <BRANCH [default=mbmesh-redist]> --esmfmkfile <ESMFMKFILE> --platform <PLATFORM [Darwin(default), Linux, Cheyenne]> --runs <RUNS [default=1]'")

    np = args.__dict__["np"]
    testcase = args.__dict__["testcase"]
    branch = args.__dict__["branch"]
    esmfmkfile = args.__dict__["esmfmkfile"]
    platform = args.__dict__["platform"]
    runs = args.__dict__["runs"]

    # add config directory to sys.path, regardless of where this script was called from originally
    sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "config"))

    # import platform specific specific parameters
    config = __import__(platform)
    ESMFDIR = config.ESMFDIR
    RUNDIR = config.RUNDIR
    SRCDIR = config.SRCDIR

    # import testcase specific platform parameters
    args = config.testcase_args[testcase]
    GRID1 = args["GRID1"]
    GRID2 = args["GRID2"]

    print("ESMFDIR = ", ESMFDIR)
    print("RUNDIR = ", RUNDIR)
    print("SRCDIR = ", SRCDIR)
    print("Testcase (", testcase, ") input parameters:")
    print("  GRID1 = ", GRID1)
    print("  GRID2 = ", GRID2)
    print("\n")

    procs=(36, 72, 144, 288, 576, 1152, 2304, 4608)

    # 1 initialize: build and install esmf and tests with appropriate env vars
    try:
        import initTest
        ESMFMKFILE = initTest.build_esmf(ESMFDIR, RUNDIR, SRCDIR, testcase, esmfmkfile=esmfmkfile, platform=platform, branch=branch)
        initTest.build_test(ESMFMKFILE, RUNDIR, SRCDIR, testcase, platform=platform)
    except:
        raise RuntimeError("Error building the tests.")

    # 2 run: submit the test runs
    try:
        import runTest
        EXECDIR = runTest.setup(SRCDIR, RUNDIR, np, runs, testcase, procs, GRID1, GRID2, platform=platform)
        runTest.run(procs, np, SRCDIR, EXECDIR, platform=platform)
    except:
        raise RuntimeError("Error submitting the tests.")

    # 3 post: collect the results into csv files
    if sys.version_info < (3, 5):
        raise EnvironmentError ("Sorry, Python 3.5 or higher is required for test result collection.")

    try:
        import collectResults
        timingfile = collectResults.timing(EXECDIR, np, runs, testcase, procs, platform=platform)
        memoryfile = collectResults.memory(EXECDIR, np, runs, testcase, procs, platform=platform)

        print ("Results are in the following files:\n", timingfile, "\n", memoryfile)
    except:
        raise RuntimeError("Error collecting the test results.")

# # 4 report: manual, scp, copy and paste the files into drive spreadsheet and make the appropriate graphs
# 
# # scp rokuingh@cheyenne.ucar.edu:/glade/work/rokuingh/MBMeshPerformanceResults/runs/<num>/mbmesh_$testcase_timing_profile_results.csv .
# # more mbmesh_$testcase_timing_profile_results.csv | xclip -sel clip
# # scp rokuingh@cheyenne.ucar.edu:/glade/work/rokuingh/MBMeshPerformanceResults/runs/<num>/mbmesh_$testcase_memory_profile_results.csv .
# # more mbmesh_$testcase_memory_profile_results.csv | xclip -sel clip
