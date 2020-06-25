#!/usr/bin/python
# coding: utf-8
#

import os, re
from subprocess import Popen
from shutil import copy2
from time import localtime, strftime
from math import floor


def generate_id(ROOTDIR):
    import os, re

    RUNDIR = os.path.join(ROOTDIR, "runs")

    if not os.path.isdir(RUNDIR):
        try:
            os.makedirs(RUNDIR)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    dirnums = []
    for path in os.listdir(RUNDIR):
        directory = os.path.join(RUNDIR, path)
        if os.path.isdir(directory):
            head, tail = os.path.split(directory)
            dirnums.append(int(tail))

    EXECDIR = os.path.join(RUNDIR, str(max(dirnums or [0]) + 1))

    if not os.path.isdir(EXECDIR):
        try:
            os.makedirs(EXECDIR)
        except OSError as exc: # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    return (EXECDIR)

# source: http://code.activestate.com/recipes/81330/
def multiple_replace(dict, text):
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, dict.keys())))

  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: dict[mo.string[mo.start():mo.end()]], text) 

def setup(SRCDIR, RUNDIR, np, runs, testcase, procs, GRID1, GRID2, cheyenne=False):

    try:
        if not cheyenne: procs = [np]
        EXECDIR = generate_id(RUNDIR)

        # run all cases in procs that are not larger than input
        for pnum in procs:
            if pnum <= np:

                # calculate the number of nodes required for this batch submission
                nnum = floor((pnum+36-1)/36)
    
                # build the qsub file
                replacements = {"%np%" : str(pnum),
                                "%nn%" : str(nnum),
                                "%nrun%" : str(runs),
                                "%EXECDIR%" : EXECDIR,
                                "%grid1%" : GRID1,
                                "%grid2%" : GRID2,
                                "#cheyenne# " : ""}

                if not cheyenne:
                    replacements["#cheyenne# "] = "# "
                    replacements["#test# "] = ""

                with open(os.path.join(SRCDIR, "runProfile.pbs")) as text:
                    new_text = multiple_replace(replacements, text.read())
                with open(os.path.join(EXECDIR, "runProfile"+str(pnum)+".pbs"), "w") as result:
                    result.write(new_text)

                for ind in range(1,runs+1):
                    # create a separate directory to run each executable nrun times to  give
                    PROCRUNDIR = os.path.join(EXECDIR,str(pnum)+"-"+str(ind))
                    if not os.path.isdir(PROCRUNDIR):
                        try:
                            os.makedirs(PROCRUNDIR)
                        except OSError as exc: # Guard against race condition
                            if exc.errno != errno.EEXIST:
                                raise
                    # copy config files and executable to execution directory
                    copy2(os.path.join(SRCDIR,testcase,"MOAB_eval_"+testcase), os.path.join(PROCRUNDIR,"MOAB_eval"))

    except:
        raise RuntimeError ("Error setting up execution directory.")

    return EXECDIR


def run(procs, np, EXECDIR, cheyenne=False):
    try:
        print ("\nSubmit the test runs (<15 minutes):", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

        if not cheyenne: procs = [np]

        job_ids = []
        for pnum in procs:
            if pnum <= np:

                rc = 0
                if cheyenne:
                    # don't block these jobs, chaser will depend on them to finish successfully before starting
                    qsub_command = ["qsub", os.path.join(EXECDIR, "runProfile"+str(pnum)+".pbs")]
                    tmp = Popen(qsub_command)
                    streamdata = tmp.communicate()[0]
                    rc = tmp.returncode
                    job_ids.append(rc)
                else:
                    tmp = Popen(["bash", os.path.join(EXECDIR, "runProfile"+str(pnum)+".pbs")])
                    streamdata = tmp.communicate()[0]
                    rc = tmp.returncode

                    if rc != 0:
                        raise RuntimeError("Error in test job submissions (code {0}): {1}".format(str(rc), qsub_command))

        if cheyenne:
            # chaser job will only start after all previous jobs have completed, indicates that result collection may continue
            qsub_command = ["qsub", "-W depend=afterok", [id for id in job_ids], os.path.join(EXECDIR, "chaser.pbs")]
            tmp = Popen(["bash", os.path.join(EXECDIR, "runProfile"+str(pnum)+".pbs")])
            streamdata = tmp.communicate()[0]
            rc = tmp.returncode
            
            print ("All jobs completed successfully.", strftime("%a, %d %b %Y %H:%M:%S", localtime()))

            # don't check rc here because we want to proceed regardless of what happens with the chaser
    
    except:
        raise RuntimeError("Error submitting the tests.")
