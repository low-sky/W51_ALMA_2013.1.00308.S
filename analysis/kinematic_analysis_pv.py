import numpy as np
import pvextractor
import os
import glob
import paths
from astropy import units as u
from astropy import coordinates
from astropy import wcs
from spectral_cube import SpectralCube
import pyregion

# use outflow_meta b/c higher precision than ds9 reg
from outflow_meta import e2e, e8, north, lacy
from line_point_offset import offset_to_point

import pylab as pl

#fntemplate = 'full_W51e2cutout_spw{0}_lines.fits'
#medsubtemplate = 'full_W51e2cutout_spw{0}_lines_medsub.fits'

## the c&p approach is stupid compared to the LB approach that reads the reg files...
## c&p'd from ../regions/e2e_disk_pvextract.reg  ../regions/north_disk_pvextract.reg
#northdiskycoords = "19:23:40.177,+14:31:06.50,19:23:39.923,+14:31:04.52".split(",")
## orthogonal to SiO outflow
#northdiskycoords = "19:23:40.069,+14:31:06.10,19:23:40.039,+14:31:04.90".split(",")
#
## perpendicular to outflow (ish)
#e2diskycoords = "19:23:44.197,+14:30:37.34,19:23:43.960,+14:30:34.55,19:23:43.882,+14:30:32.21,19:23:43.851,+14:30:31.26".split(",")
## perpendicular to SiO outflow
#e2diskycoords = "19:23:44.032,+14:30:36.29,19:23:43.909,+14:30:32.90".split(",")
#
## big, perp to CO (very, very coarsely)
#e8diskycoords = "19:23:43.913,+14:30:29.96,19:23:43.874,+14:30:26.09".split(",")
## small, perp to SiO outflow
#e8diskycoords = "19:23:43.928,+14:30:29.17,19:23:43.882,+14:30:27.18".split(",")

for ii,direction in enumerate(('perpco', 'perpsio')):
    diskycoorddict = {}
    for source in ('e2e','e8','north','lacy'):
        diskycoord_list = pyregion.open(paths.rpath("{0}_disk_pvextract.reg"
                                                    .format(source)))[ii].coord_list
        diskycoords = coordinates.SkyCoord(["{0} {1}".format(diskycoord_list[jj],
                                                             diskycoord_list[jj+1])
                                            for jj in range(0,
                                                            len(diskycoord_list),
                                                            2)], unit=(u.deg,
                                                                       u.deg),
                                           frame='fk5')
        diskycoorddict[source] = diskycoords

    diskycoorddict['e2'] = diskycoorddict['e2e']

    for name, cutoutname, source, vrange in (
        ('lacy', 'north', lacy, (50,75)),
        ('north', 'north', north, (45,75)),
        ('e8', 'e8', e8, (45,75)),
        ('e2', 'e2', e2e, (45,70)),
       ):

        diskycoords = diskycoorddict[name]

        for fn in glob.glob(paths.dpath("12m/cutouts/W51_b6_12M*{0}*fits".format(cutoutname))):

            namesplit = fn.split(".")
            if cutoutname not in namesplit[3]:
                # e2 matches Acetone21120...
                continue

            assert 'cutout' in fn
            basename = ".".join([os.path.basename(namesplit[0]),
                                 namesplit[1],
                                 name+"_diskpv",
                                 "fits"])
            outfn = paths.dpath(os.path.join("12m/pv/", basename))

            print("Extracting {0} {2}: {1}".format(fn, direction, name))

            cube = SpectralCube.read(fn)
            cube.allow_huge_operations=True
            cube.beam_threshold = 5
            med = cube.median(axis=0)
            medsub = cube - med

            extraction_path = pvextractor.Path(diskycoords, 0.2*u.arcsec)
            extracted = pvextractor.extract_pv_slice(medsub, extraction_path)
            #extracted.writeto(outfn, clobber=True)

            ww = wcs.WCS(extracted.header)
            ww.wcs.cdelt[1] /= 1000.0
            ww.wcs.crval[1] /= 1000.0
            ww.wcs.cunit[1] = u.km/u.s
            ww.wcs.cdelt[0] *= 3600
            ww.wcs.cunit[0] = u.arcsec

            fig = pl.figure(1)
            fig.clf()
            ax = fig.add_axes([0.15, 0.1, 0.8, 0.8],projection=ww)
            ax.imshow(extracted.data, cmap='viridis')
            ax.set_xlabel("Offset [\"]")
            ax.set_ylabel("$V_{LSR}$ [km/s]")

            good_limits = (np.argmax(np.isfinite(extracted.data.max(axis=0))),
                           extracted.data.shape[1] -
                           np.argmax(np.isfinite(extracted.data.max(axis=0)[::-1])))
            leftmost_position = ww.wcs_pix2world(good_limits[0],
                                                 vrange[0],
                                                 0)[0]*u.arcsec

            trans = ax.get_transform('world')
            length = (1000*u.au / (5400*u.pc)).to(u.deg, u.dimensionless_angles())
            endpoints_x = u.Quantity([0.5*u.arcsec, 0.5*u.arcsec+length]) + leftmost_position
            ax.plot(endpoints_x.to(u.arcsec),
                    [vrange[0]+5]*2*u.km/u.s,
                    'w',
                    transform=trans,
                    zorder=100, linewidth=2)
            ax.text(endpoints_x.mean().value,
                    (vrange[0]+6),
                    "1000 au", color='w', transform=trans, ha='center')

            origin = offset_to_point(source.ra.deg,
                                     source.dec.deg,
                                     extraction_path)*u.deg

            ax.vlines(origin.to(u.arcsec).value, vrange[0]-5, vrange[1]+5,
                      color='w', linestyle='--', linewidth=2.0,
                      alpha=0.6, transform=trans)

            ax.set_ylim(ww.wcs_world2pix(0,vrange[0],0)[1],
                        ww.wcs_world2pix(0,vrange[1],0)[1])
            ax.set_xlim(good_limits)


            # ax.set_aspect(4)
            ax.set_aspect(2*extracted.data.shape[1]/extracted.data.shape[0])



            fig.savefig(paths.fpath('pv/{0}/{1}'.format(name, direction) +
                                    basename.replace(".fits",".png")),
                        bbox_inches='tight')


            #outflow_coords = coordinates.SkyCoord(["19:23:44.127 +14:30:32.30", "19:23:43.822 +14:30:36.64"], unit=(u.hour, u.deg), frame='fk5')
            #outflowpath = pvextractor.Path(outflow_coords, 0.2*u.arcsec)
            #extracted = pvextractor.extract_pv_slice(medsub, outflowpath)
            #extracted.writeto('W51e2_PV_outflowaxis_spw{0}.fits'.format(ii), clobber=True)
