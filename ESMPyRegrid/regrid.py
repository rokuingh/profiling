# This is an ESMPy benchmarking utility
import ESMF
import numpy as np

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

    lon_par2d, lat_par2d = np.meshgrid(lon_par, lat_par, indexing="ij")

    #import ipdb; ipdb.set_trace()

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


# Start up ESMF, this call is only necessary to enable debug logging
#esmpy = ESMF.Manager(debug=True)

DATADIR = "/glade/p/work/rokuingh/data/"
#DATADIR = "/Users/ryan.okuinghttons/netCDFfiles/grids/"
grid1 = [DATADIR+"hycom_grid1.nc", ESMF.FileFormat.GRIDSPEC]
#grid1 = [DATADIR+"ll2.5deg_grid.nc", ESMF.FileFormat.SCRIP]
grid2 = [DATADIR+"tx0.1v2_nomask.nc", ESMF.FileFormat.SCRIP]
#grid2 = [DATADIR+"T42_grid.nc", ESMF.FileFormat.SCRIP]


# Create a destination grid from a GRIDSPEC formatted file.
srcgrid = ESMF.Grid(filename=grid1[0], filetype=grid1[1], add_corner_stagger=True)

dstgrid = ESMF.Grid(filename=grid2[0], filetype=grid2[1], add_corner_stagger=True)

srcfield = ESMF.Field(srcgrid, "srcfield", staggerloc=ESMF.StaggerLoc.CENTER)
xctfield = ESMF.Field(srcgrid, "xctfield", staggerloc=ESMF.StaggerLoc.CENTER)
dstfield = ESMF.Field(dstgrid, "dstfield", staggerloc=ESMF.StaggerLoc.CENTER)

srcfield = initialize_field(srcfield)
xctfield = initialize_field(xctfield)

# Regrid from source grid to destination grid.
regridSrc2Dst = ESMF.Regrid(srcfield, dstfield,
                            regrid_method=ESMF.RegridMethod.CONSERVE,
                            unmapped_action=ESMF.UnmappedAction.IGNORE)

dstfield = regridSrc2Dst(srcfield, dstfield)

regridSrc2Dst = ESMF.Regrid(dstfield, srcfield,
                            regrid_method=ESMF.RegridMethod.CONSERVE,
                            unmapped_action=ESMF.UnmappedAction.IGNORE)

srcfield = regridSrc2Dst(dstfield, srcfield)

print "Interpolation error = {}".format(np.sum(np.abs(srcfield.data - xctfield.data)/np.abs(xctfield.data))/xctfield.size)

#plot(srclons, srclats, srcfield, dstlons, dstlats, dstfield)
