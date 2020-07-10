import os

ESMFDIR="/glade/work/rokuingh/sandbox/esmf"
RUNDIR="/glade/work/rokuingh/MBMeshPerformanceResults"
SRCDIR="/glade/work/rokuingh/sandbox/profiling/Moab"

testcase_args = dict(
    create = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.esmf.nc"),
                  GRID2 = os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.esmf.nc")),
    dual = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1x2e0deg10e4node.esmf.nc"),
                GRID2 = os.path.join(SRCDIR,"data", "ll1x2e0deg10e4node.esmf.nc")),
    grid2mesh = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.scrip.nc"),
                     GRID2 = os.path.join(SRCDIR,"data", "ll1x2e4deg10e7node.scrip.nc")),
    redist = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc"),
                  GRID2 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc")),
    regridbilinear = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc"),
                          GRID2 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc")),
    regridconservative = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc"),
                              GRID2 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc")),
    rendezvous = dict(GRID1 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc"),
                      GRID2 = os.path.join(SRCDIR,"data", "ll1x2e3deg10e6node.esmf.nc"))
)