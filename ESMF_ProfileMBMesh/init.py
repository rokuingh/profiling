#!/usr/bin/python
# coding: utf-8
#

import sys, os, re
from shutil import copy2
from subprocess import check_call
from time import localtime, strftime

def esmf(config, testcase, platform, branch, esmfmkfile, gnu10):
    ESMFMKFILE=""
    if (esmfmkfile != ""):
        try:
            # verify validity of ESMFMKFILE before accepting
            accept = False
            with open(esmfmkfile) as esmfmkf:
                for line in esmfmkf:
                    if "ESMF environment variables pointing to 3rd party software" in line: accept = True
            if accept:
                print ("\nSkip ESMF build, esmf.mk provided.")
                ESMFMKFILE = esmfmkfile
            else:
                print ("\nSorry, there is something wrong with the provided esmf.mk, please check it and resubmit: ", esmfmkfile)
                raise EnvironmentError
        except EnvironmentError as err:
            raise
    else:
        try:
            print ("\nBuild and install ESMF (<30 minutes):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

            RUNDIR = config.RUNDIR
            SRCDIR = config.SRCDIR
            ESMF_OS = config.esmf_env["ESMF_OS"]
            ESMF_COMPILER = config.esmf_env["ESMF_COMPILER"]
            ESMF_COMM = config.esmf_env["ESMF_COMM"]
            ESMF_NETCDF = config.esmf_env["ESMF_NETCDF"]
            ESMF_NETCDF_INCLUDE = config.esmf_env["ESMF_NETCDF_INCLUDE"]
            ESMF_NETCDF_LIBPATH = config.esmf_env["ESMF_NETCDF_LIBPATH"]
            ESMF_BOPT = config.esmf_env["ESMF_BOPT"]
            ESMF_OPTLEVEL = config.esmf_env["ESMF_OPTLEVEL"]
            ESMF_ABI = config.esmf_env["ESMF_ABI"]
            ESMF_BUILD_NP = config.esmf_env["ESMF_BUILD_NP"]


            # call from RUNDIR to avoid polluting execution dir with output files 
            BUILDDIR = os.path.join(RUNDIR, testcase)
            if not os.path.isdir(BUILDDIR):
                try:
                    os.makedirs(BUILDDIR)
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            os.chdir(BUILDDIR)
            copy2(os.path.join(SRCDIR,"buildESMF.pbs"), BUILDDIR)

            # checkout ESMF
            esmfgitrepo = "https://github.com/esmf-org/esmf.git"
            ESMFDIR = os.path.join(BUILDDIR, "esmf")
            if not os.path.isdir(ESMFDIR):
                try:
                    check_call(["git", "clone", esmfgitrepo])
                except OSError as exc: # Guard against race condition
                    if exc.errno != errno.EEXIST:
                        raise
            
            os.chdir(ESMFDIR)
            check_call(["git", "checkout", branch])

            # write the pbs script
            pbscript = [os.path.join(BUILDDIR, "buildESMF.pbs"), testcase, ESMFDIR, branch, ESMF_OS, ESMF_COMPILER, ESMF_COMM, ESMF_NETCDF, ESMF_NETCDF_INCLUDE, ESMF_NETCDF_LIBPATH, ESMF_BOPT, str(ESMF_OPTLEVEL), str(ESMF_ABI), str(ESMF_BUILD_NP), str(gnu10)]

            # set up the pbs script for submission to qsub on cheyenne or bash otherwise
            if platform == "Cheyenne":
                run_command = ["qsub", "-W", "block=true"] + pbscript
            else:  
                run_command = ["bash"] + pbscript

            check_call(run_command)

            # buildESMF.pbs writes location of esmf.mk to $ESMFDIR/esmfmkfile.out
            with open (os.path.join(ESMFDIR, "esmfmkfile.out"), "r") as esmfmkfileobj:
                ESMFMKFILE = esmfmkfileobj.read().replace("\n","")
            print ("ESMF build and installation success.", strftime("%a, %d %b %Y %H:%M:%S", localtime()))
        except:
            raise RuntimeError("Error building ESMF installation.")

    return ESMFMKFILE


def test(ESMFMKFILE, config, testcase, platform):
    RUNDIR = config.RUNDIR
    SRCDIR = config.SRCDIR

    try:
        print ("Build test executable")
        test_command = ["bash", os.path.join(SRCDIR, "buildTest.pbs"), ESMFMKFILE, RUNDIR, SRCDIR, testcase, platform]
        check_call(test_command)
    except:
        raise RuntimeError("Error building test executable.")

