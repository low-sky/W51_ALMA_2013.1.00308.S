"""
Joint imaging of 7m and 12m data
"""
import os

calpath = './'

vistemplate = 'calibrated_{0}.ms'
vis_7m='calibrated_7m.ms'
vis_tc='calibrated_12m.ms'

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
               ('C18O2-1', "219.56036GHz", 1.2,),
               ('CH3OCHO17314-16313E','218.28083GHz',0.5),
               ('CH3CH2CN24321-23320','218.39002GHz',0.5),
               ('HC3Nv7=1_24-23','218.86063GHz',1.2),
               ('Acetone21120-20219AE','219.21993GHz',1.2),
               ('Acetone21120-20119EE','219.24214GHz',1.2),
               ('CH3CH2CN24222-23221','219.50559GHz',1.2),
               ('H213CO312-211','219.90849GHz',1.2),
               ('H2CN303-202_F3_2','219.98449GHz',1.2),
               ('H2CN322-221_F5_2','219.99422GHz',1.2),
               ('CH3OCHO17413-16412A','220.19027GHz',1.2),
               ('CH3CH2OH550-541','231.02517GHz',1.2),
               ('CH3OCH313013-12112AA','231.98772GHz',1.2),
               ('NH2CHO1156-1055','233.59451GHz',1.2),
                      ):

    outms_template = "{line}_W51_B6_{array}.cvel.ms"
    concatvis = "{line}_W51_B6_cvel_merge.ms".format(line=line)

    nchans = int((velocity_range[1]-velocity_range[0])/velocity_res)

    # cvel the data first
    for array in ('7m','12m'):
        outputvis = outms_template.format(line=line, array=array)
        if not os.path.exists(outputvis):
            cvel2(vis=os.path.join(calpath, vistemplate.format(array)),
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

    if not os.path.exists(concatvis):
        concat(vis=[outms_template.format(line=line, array=array) for array in ('7m','12m')],
               concatvis=concatvis)

    assert os.path.exists(concatvis)

    output = 'W51_b6_7M_12M.{0}'.format(line)

    if not os.path.exists(output+".image.pbcor.fits"):
        os.system('rm -rf ' + output + '*/')
        tclean(vis=concatvis,
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
               imsize=[3200,3200],
               cell='.05arcsec',
               weighting='briggs',
               robust=0.5,
               phasecenter='',
               threshold='15mJy',
               savemodel='none',
               uvtaper=True,
               innteraper=['10arcsec'],
              )
        myimagebase = output
        impbcor(imagename=myimagebase+'.image', pbimage=myimagebase+'.pb', outfile=myimagebase+'.image.pbcor', overwrite=True)
        exportfits(imagename=myimagebase+'.image.pbcor', fitsimage=myimagebase+'.image.pbcor.fits', overwrite=True, dropdeg=True)
        exportfits(imagename=myimagebase+'.pb', fitsimage=myimagebase+'.pb.fits', overwrite=True, dropdeg=True)
        exportfits(imagename=myimagebase+'.residual', fitsimage=myimagebase+'.residual.fits', overwrite=True, dropdeg=True)

        for suffix in ('pb', 'weight', 'sumwt', 'psf', 'model', 'mask',
                       'image', 'residual'):
            os.system('rm -rf {0}.{1}'.format(output, suffix))

