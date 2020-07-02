#!/usr/bin/python
# coding: utf-8
#

import sys, os, re
from subprocess import check_call
from time import localtime, strftime

# source: http://code.activestate.com/recipes/81330/
def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def build_esmf(ESMFDIR, RUNDIR, SRCDIR, testcase, esmfmkfile="", cheyenne=False):
    # # 1.2 initialize: build and install ESMF
    ESMFMKFILE=esmfmkfile
    try:
        if (esmfmkfile == ""):
            print ("\nBuild and install ESMF (<30 minutes):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

            # build the pbs script
            replacements = {"%testcase%" : testcase,
                            "%rundir%" : RUNDIR,
                            "%esmfdir%" : ESMFDIR}
            if cheyenne:
                replacements["#cheyenne# "] = ""
            else:
                replacements["#test# "] = ""

            # write the pbs script
            pbscript = os.path.join(RUNDIR, "buildESMF-"+testcase+".pbs")
            with open(os.path.join(SRCDIR, "buildESMF.pbs")) as text:
                new_text = multiple_replace(replacements, text.read())
            with open(pbscript, "w") as result:
                result.write(new_text)

            # set up the pbs script for submission to qsub on cheyenne or bash otherwise
            if cheyenne:
                run_command = ["qsub", "-W block=true"] + [pbscript]
            else:  
                run_command = ["bash"] + [pbscript]

            check_call(run_command)

            # this is a bit hardcoded.. buildESMF.pbs writes location of esmf.mk to following file
            with open (os.path.join(RUNDIR, testcase, "esmfmkfile.out"), "r") as esmfmkfileobj:
                ESMFMKFILE = esmfmkfileobj.read().replace("\n","")
            print ("ESMF build and installation success.", strftime("%a, %d %b %Y %H:%M:%S", localtime()))
        else:
            ESMFMKFILE = esmfmkfile
            print ("\nSkip ESMF build, esmf.mk provided.")
    except:
        raise RuntimeError("Error building ESMF installation.")

    return ESMFMKFILE


def build_test(SRCDIR, ESMFMKFILE, testcase, cheyenne=False):
    # # 1.2 initialize: build the test executable
    try:
        print ("Build test executable")
        test_command = ["bash", os.path.join(SRCDIR, "buildTest.bash"), testcase, ESMFMKFILE, SRCDIR, str(cheyenne)]
        check_call(test_command)
    except:
        raise RuntimeError("Error building test executable.")

