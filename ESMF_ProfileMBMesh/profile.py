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
import click

@click.command()
@click.option('-np', type=int, required=True, help='Number of processing cores')
@click.option('-testcase', type=str, required=True, help='Test case  [create,dual,grid2mesh,redist,regridbilinear,regridconservative,rendezvous]')
@click.option('--branch', type=str, default="mbmesh-redist", help='Branch of the ESMF repo to use')
@click.option('--esmfmkfile', type=str, default="", help='Path to esmf.mk, will build ESMF if not supplied')
@click.option('--platform', type=str, default="Darwin", help='Platform configuration [Cheyenne, Darwin, Linux]')
@click.option('--runs', type=int, default=1, help='Number of runs')
@click.option('--gnu10', is_flag=True, default=False, help='Fix for gnu10 ESMF compiler options')
def cli(np, testcase, branch, esmfmkfile, platform, runs, gnu10):
    # Raw print arguments
    print("\nRunning 'profile.py' with following input parameter values: ")
    print("-np = ", np)
    print("-testcase = ", testcase)
    print("--branch = ", branch)
    print("--esmfmkfile = ", esmfmkfile)
    print("--platform = ", platform)
    print("--runs = ", runs)
    print("--gnu10 = ", gnu10)

    # add config directory to sys.path, regardless of where this script was called from originally
    sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "config"))

    # import platform specific specific parameters
    config = __import__(platform)
    RUNDIR = config.RUNDIR
    SRCDIR = config.SRCDIR

    # import testcase specific platform parameters
    args = config.testcase_args[testcase]
    GRID1 = args["GRID1"]
    GRID2 = args["GRID2"]

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
        ESMFMKFILE = initTest.build_esmf(RUNDIR, SRCDIR, testcase, platform, branch, esmfmkfile, gnu10)
        initTest.build_test(ESMFMKFILE, RUNDIR, SRCDIR, testcase, platform)
    except:
        raise RuntimeError("Error building the tests.")

    # 2 run: submit the test runs
    try:
        import runTest
        EXECDIR = runTest.setup(SRCDIR, RUNDIR, np, runs, testcase, procs, GRID1, GRID2, platform)
        runTest.run(procs, np, SRCDIR, EXECDIR, platform)
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


if __name__ == '__main__':
    cli()