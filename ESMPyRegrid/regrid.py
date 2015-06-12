# This is an ESMPy benchmarking utility
import ESMF
import numpy as np
from mpi4py import MPI
import time
import sys

def create_grid_corners(lons, lats, lonbnds, latbnds):
    [lon, lat] = [0, 1]
    max_index = np.array([len(lons), len(lats)])
    grid = ESMF.Grid(max_index,
                     staggerloc=[ESMF.StaggerLoc.CENTER, ESMF.StaggerLoc.CORNER])

    gridXCenter = grid.get_coords(lon)
    lon_par = lons[grid.lower_bounds[ESMF.StaggerLoc.CENTER][lon]:grid.upper_bounds[ESMF.StaggerLoc.CENTER][lon]]
    gridXCenter[...] = lon_par.reshape((lon_par.size, 1))

    gridYCenter = grid.get_coords(lat)
    lat_par = lats[grid.lower_bounds[ESMF.StaggerLoc.CENTER][lat]:grid.upper_bounds[ESMF.StaggerLoc.CENTER][lat]]
    gridYCenter[...] = lat_par.reshape((1, lat_par.size))

    lbx = grid.lower_bounds[ESMF.StaggerLoc.CORNER][lon]
    ubx = grid.upper_bounds[ESMF.StaggerLoc.CORNER][lon]
    lby = grid.lower_bounds[ESMF.StaggerLoc.CORNER][lat]
    uby = grid.upper_bounds[ESMF.StaggerLoc.CORNER][lat]

    gridXCorner = grid.get_coords(lon, staggerloc=ESMF.StaggerLoc.CORNER)
    for i0 in range(ubx - lbx - 1):
        gridXCorner[i0, :] = lonbnds[i0, 0]
    gridXCorner[i0 + 1, :] = lonbnds[i0, 1]

    gridYCorner = grid.get_coords(lat, staggerloc=ESMF.StaggerLoc.CORNER)
    for i1 in range(uby - lby - 1):
        gridYCorner[:, i1] = latbnds[i1, 0]
    gridYCorner[:, i1 + 1] = latbnds[i1, 1]

    return grid

def initialize_field(field):
    realdata = False
    if realdata:
        try:
            import netCDF4 as nc

            f = nc.Dataset('charles.nc')
            swcre = f.variables['swcre']
            swcre = swcre[:]
        except:
            raise ImportError('netCDF4 not available on this machine')

        field.data[...] = swcre.T
    else:
        field.data[...] = 2.0

    return field

def compute_mass(valuefield, areafield, fracfield, dofrac):
    mass = 0.0
    areafield.get_area()
    if dofrac:
        mass = np.sum(areafield*valuefield*fracfield)
    else:
        mass = np.sum(areafield * valuefield)

    return mass

def plot(srclons, srclats, srcfield, dstlons, dstlats, interpfield):

    try:
        import matplotlib
        import matplotlib.pyplot as plt
    except:
        raise ImportError("matplotlib is not available on this machine")

    fig = plt.figure(1, (15, 6))
    fig.suptitle('ESMPy Conservative Regridding', fontsize=14, fontweight='bold')

    ax = fig.add_subplot(1, 2, 1)
    im = ax.imshow(srcfield.T, vmin=-140, vmax=0, cmap='gist_ncar', aspect='auto',
                   extent=[min(srclons), max(srclons), min(srclats), max(srclats)])
    ax.set_xbound(lower=min(srclons), upper=max(srclons))
    ax.set_ybound(lower=min(srclats), upper=max(srclats))
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Source Data")

    ax = fig.add_subplot(1, 2, 2)
    im = ax.imshow(interpfield.T, vmin=-140, vmax=0, cmap='gist_ncar', aspect='auto',
                   extent=[min(dstlons), max(dstlons), min(dstlats), max(dstlats)])
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Conservative Regrid Solution")

    fig.subplots_adjust(right=0.8)
    cbar_ax = fig.add_axes([0.9, 0.1, 0.01, 0.8])
    fig.colorbar(im, cax=cbar_ax)

    plt.show()

##########################################################################################


# use debugging?
esmpy = ESMF.Manager(debug=False)
# mpi comm handle
comm = MPI.COMM_WORLD
# regrid method from input argument
rm = int(sys.argv[1])

# create a benchmark deque
bm = []

grid1 = None
grid2 = None
# local initialize data
if len(sys.argv) == 3:
    if int(sys.argv[2]) == 1:
        DATADIR = "/Users/ryan.okuinghttons/netCDFfiles/grids/"
        grid1 = [DATADIR+"ll2.5deg_grid.nc", ESMF.FileFormat.SCRIP]
        grid2 = [DATADIR+"T42_grid.nc", ESMF.FileFormat.SCRIP]
# yellowstone initialize data
else:
    DATADIR = "/glade/p/work/rokuingh/data/"
    grid1 = [DATADIR+"hycom_grid1.nc", ESMF.FileFormat.GRIDSPEC]
    grid2 = [DATADIR+"tx0.1v2_nomask.nc", ESMF.FileFormat.SCRIP]

# Create Grids

# timing
start = time.time()

srcgrid = None
if rm == ESMF.RegridMethod.CONSERVE:
    srcgrid = ESMF.Grid(filename=grid1[0], filetype=grid1[1], add_corner_stagger=True)
else:
    srcgrid = ESMF.Grid(filename=grid1[0], filetype=grid1[1])

# timing
end = time.time()
bm.append(('grid1create', start, end))
start = time.time()

dstgrid = None
if rm == ESMF.RegridMethod.CONSERVE:
    dstgrid = ESMF.Grid(filename=grid2[0], filetype=grid2[1], add_corner_stagger=True)
else:
    dstgrid = ESMF.Grid(filename=grid2[0], filetype=grid2[1])

# timing
end = time.time()
bm.append(('grid2create', start, end))

# Create and initialize Fields

srcfield = ESMF.Field(srcgrid, "srcfield", staggerloc=ESMF.StaggerLoc.CENTER)
xctfield = ESMF.Field(dstgrid, "xctfield", staggerloc=ESMF.StaggerLoc.CENTER)
dstfield = ESMF.Field(dstgrid, "dstfield", staggerloc=ESMF.StaggerLoc.CENTER)

srcfield = initialize_field(srcfield)
xctfield = initialize_field(xctfield)

# barrier before regrid store
comm.Barrier()

# timing
start = time.time()

# Regrid from source grid to destination grid
regridSrc2Dst = ESMF.Regrid(srcfield, dstfield,
                            regrid_method=rm,
                            pole_method=ESMF.PoleMethod.NONE,
                            unmapped_action=ESMF.UnmappedAction.IGNORE,
                            ignore_degenerate=True)

# timing
end = time.time()
bm.append(('regrid store', start, end))

# barrier before regrid application
comm.Barrier()

# timing
start = time.time()

# Apply regridding weights
dstfield = regridSrc2Dst(srcfield, dstfield)

# timing
end = time.time()
bm.append(('regrid run', start, end))

# Compute pointwise relative error
relerr = np.sum(np.abs(dstfield.data - xctfield.data)/np.abs(xctfield.data))
num_nodes = xctfield.size

# clean up timings
timings = []
titles = []
for x, y, z in bm:
    titles.append(x)
    timings.append(z-y)

# handle the parallel case
if esmpy.pet_count > 1:
    try:
        from mpi4py import MPI
    except:
        raise ImportError
    comm = MPI.COMM_WORLD
    relerr = comm.reduce(relerr, op=MPI.SUM)
    num_nodes = comm.reduce(num_nodes, op=MPI.SUM)
    timings = comm.reduce(timings, op=MPI.MAX)

# Output results and verify error is reasonable
import os.path
output_file = "performance_testing.out"
header = "ESMPy Regrid Performance Testing"
of_present = os.path.isfile(output_file)

f = open('performance_testing.out', 'a')
if esmpy.local_pet == 0:
    if not of_present:
        f.write(header+"\n\n")
        f.write("grid 1\t"+grid1[0]+"\n")
        f.write("grid 2\t"+grid2[0]+"\n\n")
        f.write("processors\t")
        for x in range(len(titles)):
            f.write(str(titles[x])+"\t")
        f.write("regrid method\t")
        f.write("Regridding error\t")
        f.write("\n")
    f.write(str(esmpy.pet_count)+"\t")
    for x in range(len(titles)):
        f.write(str(timings[x])+"\t")
    f.write(str(rm)+"\t"+str(relerr/num_nodes)+"\n")
f.close()

#plot(srclons, srclats, srcfield, dstlons, dstlats, dstfield)

# collect garbage
srcgrid.destroy()
dstgrid.destroy()
srcfield.destroy()
dstfield.destroy()
xctfield.destroy()
regridSrc2Dst.destroy()

