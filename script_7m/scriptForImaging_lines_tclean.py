"""
Just 7m
"""
import os

calpath = './'

vis_7m='calibrated_7m.ms'

velocity_range = 25,95
velocity_res = 1.0

# It's not clear how cvel will handle overlapping SPWs

for line, restfreq, velocity_res in (
               ('H2CO303_202', "218.22219GHz",0.5,),
               ('H2CO321_220', "218.76007GHz",1.2,),
               ('H2CO322_221', "218.47564GHz",0.5,),
               ('CH3OH422-312', "218.44005GHz",0.5,),
               ('HC3N24-23', "218.32471GHz",1.2,),
               ('OCS18-17', "218.90336GHz",1.2,),
               ('OCS19-18', "231.06099GHz",1.2,),
               ('SO65-54', "219.94944GHz",1.2,),
               ('HNCO10110-919', "218.98102GHz",1.2,),
               ('HNCO1028-927', "219.73719GHz",1.2,),
               ('CH3OH423-514', "234.68345GHz",1.2,),
               ('CH3OH5m42-6m43', "234.69847GHz",1.2,),
               ('CH3OH808-716', "220.07849GHz",1.2,),
               ('13CS5-4', "231.22069GHz",1.2,),
               ('CH3OCH3_13013-12112', "231.98792GHz",1.2,),
               ('NH2CHO11210-1029', "232.27363GHz",1.2,),
               ('NH2CHO1156-1055', "233.59451GHz",1.2,),
               ('HC3Nv7=124-23', "219.17358GHz",1.2,),
               ('H30alpha', "231.90093GHz", 1.2,),
               ('C18O2-1', "219.56036GHz", 1.2,)
                      ):

    outms_template = "{line}_W51_B6_{array}.cvel.ms"
    outms = outms_template.format(line=line, array='7m')

    nchans = int((velocity_range[1]-velocity_range[0])/velocity_res)

    # cvel the data first
    for array in ('7m',):
        outputvis = outms_template.format(line=line, array=array)
        if not os.path.exists(outputvis):
            cvel2(vis=os.path.join(calpath, vis_7m),
                  outputvis=outputvis,
                  datacolumn='data',
                  field='w51',
                  mode='velocity',
                  nchan=nchans,
                  start='{0}km/s'.format(velocity_range[0]),
                  width='{0}km/s'.format(velocity_res),
                  interpolation='linear',
                  phasecenter='',
                  restfreq=restfreq,
                  outframe='LSRK',
                  veltype='radio',
                  hanning=False,)

    assert os.path.exists(outms)

    output = 'W51_b6_7M.{0}'.format(line)

    if not os.path.exists(output+".image.pbcor.fits"):
        os.system('rm -rf ' + output + '*/')
        tclean(vis=outms,
               imagename=output,
               field='w51',
               spw='',
               gridder='mosaic',
               specmode='cube',
               start='{0}km/s'.format(velocity_range[0]),
               width='{0}km/s'.format(velocity_res), interpolation='linear',
               nchan=nchans,
               restfreq=restfreq,
               veltype='radio',
               outframe='LSRK',
               interactive=F,
               niter=1000,
               imsize=[320,320],
               cell='0.5arcsec',
               weighting='briggs',
               robust=0.5,
               phasecenter='',
               threshold='15mJy',
               savemodel='none',
              )
        myimagebase = output
        impbcor(imagename=myimagebase+'.image', pbimage=myimagebase+'.pb', outfile=myimagebase+'.image.pbcor', overwrite=True)
        exportfits(imagename=myimagebase+'.image.pbcor', fitsimage=myimagebase+'.image.pbcor.fits', overwrite=True, dropdeg=True)
        exportfits(imagename=myimagebase+'.pb', fitsimage=myimagebase+'.pb.fits', overwrite=True, dropdeg=True)
        exportfits(imagename=myimagebase+'.residual', fitsimage=myimagebase+'.residual.fits', overwrite=True, dropdeg=True)
        for suffix in ('pb', 'weight', 'sumwt', 'psf', 'model', 'mask',
                       'image', 'residual'):
            os.system('rm -rf {0}.{1}'.format(output, suffix))
