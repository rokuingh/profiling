#!/usr/bin/python
# coding: utf-8
#

import sys, os, re
from subprocess import Popen
from time import localtime, strftime

# source: http://code.activestate.com/recipes/81330/
def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def build_esmf(ESMFDIR, SRCDIR, testcase, esmfmkfile="", cheyenne=False):
    # # 1.2 initialize: build and install ESMF
    ESMFMKFILE=esmfmkfile
    try:
        if (esmfmkfile == ""):
            print ("\nBuild and install ESMF (<30 minutes):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

            # build the qsub file
            replacements = {"%testcase%" : testcase,
                            "%esmfdir%" : ESMFDIR}
            if cheyenne:
                replacements["#cheyenne# "] = ""
            else:
                replacements["#test# "] = ""

            with open(os.path.join(SRCDIR, "buildESMF.pbs")) as text:
                new_text = multiple_replace(replacements, text.read())
            with open(os.path.join(ESMFDIR, "buildESMF"+testcase+".pbs"), "w") as result:
                result.write(new_text)

            qsub_command = ["qsub -sync y", os.path.join(ESMFDIR, "buildESMF"+testcase+".pbs")]

            rc = 0
            if not cheyenne:
                tmp = Popen(["bash", os.path.join(ESMFDIR, "buildESMF"+testcase+".pbs")])
                streamdata = tmp.communicate()[0]
                rc = tmp.returncode
            else:  
                tmp = Popen([qsub_command])
                streamdata = tmp.communicate()[0]
                rc = tmp.returncode

            if rc != 0:
                raise RuntimeError("ESMF install job submission error (code {0}): {1}".format(str(rc), qsub_command))
            else:
                with open (os.path.join (ESMFDIR, "esmfmkfile.out"), "r") as esmfmkfileobj:
                    ESMFMKFILE = esmfmkfileobj.read().replace("\n","")
                print ("ESMF build and installation success.", strftime("%a, %d %b %Y %H:%M:%S", localtime()))
        else:
            ESMFMKFILE = esmfmkfile
            print ("\nSkip build ESMF, esmf.mk provided.")
    except:
        raise RuntimeError("Error building ESMF installation.")

    return ESMFMKFILE


def build_test(SRCDIR, ESMFMKFILE, testcase, cheyenne=False):
    # # 1.2 initialize: build the test executable
    try:
        print ("Build test executable")
        test_command = ["bash", os.path.join(SRCDIR, "buildTest.bash"), testcase, ESMFMKFILE, SRCDIR, str(cheyenne)]

        tmp = Popen(test_command)
        streamdata = tmp.communicate()[0]
        rc = tmp.returncode
        if rc != 0:
            raise RuntimeError("Test build subprocess error (code {0}): {1}".format(str(rc), test_command))
    except:
        raise RuntimeError("Error building test executable.")

