import os

RUNDIR="/home/ryan/MBMeshPerformanceResults"
SRCDIR="/home/ryan/Dropbox/sandbox/profiling/Moab"

testcase_args = dict(
    create = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1deg.esmf.nc"),
                  GRID2 = os.path.join(SRCDIR,"data", "ll1deg.esmf.nc")),
    dual = dict(GRID1 = os.path.join(SRCDIR,"data", "ll4deg.esmf.nc"),
                GRID2 = os.path.join(SRCDIR,"data", "ll4deg.esmf.nc")),
    GRID2mesh = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1deg.scrip.nc"),
                     GRID2 = os.path.join(SRCDIR,"data", "ll1deg.scrip.nc")),
    redist = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                  GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")),
    regridbilinear = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                          GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")),
    regridconservative = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                              GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc")),
    rendezvous = dict(GRID1 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"),
                      GRID2 = os.path.join(SRCDIR,"data", "ll2deg.esmf.nc"))
)