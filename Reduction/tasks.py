import os

from AIPSData import AIPSUVData, AIPSImage
from AIPSTask import AIPSTask, AIPSList
from AIPSTV import AIPSTV

from utils import grab_catalogue, compare_catalogues, parse_params

def fitld(filename, disk, clint, sources, params=None):
    # load fits file as catalogue
    initial = grab_catalogue(disk)
    
    task = AIPSTask('FITLD')
    task.datain = os.path.realpath(filename)
    task.outdisk = disk
    task.clint = clint
    task.sources = AIPSList(sources)
    parse_params(task, params)
    task.go()
    
    final = grab_catalogue(disk)
    output = compare_catalogues(initial, final)
    return AIPSUVData(output.name, output.klass, disk, output.seq)

def msort(uvdata, params=None):
    # sort visibilities
    initial = grab_catalogue(uvdata.disk)
    
    task = AIPSTask('MSORT')
    task.indata = uvdata
    task.outdisk = uvdata.disk
    parse_params(task, params)
    task.go()
    
    final = grab_catalogue(uvdata.disk)
    output = compare_catalogues(initial, final)
    return AIPSUVData(output.name, output.klass, uvdata.disk, output.seq)

def indxr(uvdata, solint, params=None):
    # index visibilities and create empty calibration table
    task = AIPSTask('INDXR')
    task.indata = uvdata
    task.cparm[3] = solint
    parse_params(task, params)
    task.go()

def uvflg(uvdata, outfgver, params=None):
    # flags visibilities based on params
    task = AIPSTask('UVFLG')
    task.indata = uvdata
    task.outfgver = outfgver
    parse_params(task, params)
    task.go()

def clcal(uvdata, sources=None, calsour=None, params=None):
    # combine previous calibrations
    task = AIPSTask('CLCAL')
    task.indata = uvdata
    if sources:
        task.sources = AIPSList(sources)
    if calsour:
        task.calsour = AIPSList(calsour)
    parse_params(task, params)
    task.go()

def accor(uvdata, params=None):
    # correct sampler errors
    task = AIPSTask('ACCOR')
    task.indata = uvdata
    parse_params(task, params)
    task.go()

def snedt(uvdata, inext='SN', invers=0, params=None):
    # edit solution table
    tv = AIPSTV()
    tv.start()
    
    task = AIPSTask('SNEDT')
    task.indata = uvdata
    task.inext = inext
    task.invers = invers
    parse_params(task, params)
    task.go()
    
    tv.kill()

def antab(uvdata, antab_file, params=None):
    # load antenna temperature data
    task = AIPSTask('ANTAB')
    task.indata = uvdata
    task.calin = os.path.realpath(antab_file)
    parse_params(task, params)
    task.go()

def apcal(uvdata, params=None):
    # generate amplitude solutions
    task = AIPSTask('APCAL')
    task.indata = uvdata
    parse_params(task, params)
    task.go()

def bpass(uvdata, calsour, params=None):
    # generate bandpass table
    task = AIPSTask('BPASS')
    task.indata = uvdata
    task.calsour = AIPSList(calsour)
    task.bpassprm[1] = 1
    task.bpassprm[10] = 1
    parse_params(task, params)
    task.go()

def fring(uvdata, calsour, params=None): 
    # fringe fitting
    task = AIPSTask('FRING')
    task.indata = uvdata
    task.calsour = AIPSList(calsour)
    parse_params(task, params)
    task.go()

def tabed_key(uvdata, inext, invers, key, value, params=None):
    # edit table entry
    task = AIPSTask('TABED')
    task.indata = uvdata
    task.inext = inext
    task.invers = invers
    task.optype = 'KEY'
    task.aparm[4] = 3
    task.keyword = key
    task.keystrng = value
    parse_params(task, params)
    task.go()

def set_velocity(uvdata, restfreq, source, sysvel, chan, params=None):
    # set velocity parameters
    task = AIPSTask('SETJY')
    task.indata = uvdata
    task.sources = AIPSList([source])
    task.sysvel = sysvel
    task.restfreq[1], task.restfreq[2] = restfreq
    task.veltyp = 'LSR'
    task.veldef = 'RADIO'
    task.aparm[1] = chan
    parse_params(task, params)
    task.go()

def cvel_doppler(uvdata, sources, freqid=1, params=None):
    # apply Doppler correction
    initial = grab_catalogue(uvdata.disk)
    
    task = AIPSTask('CVEL')
    task.indata = uvdata
    task.sources = AIPSList(sources)
    task.freqid = freqid
    task.aparm[4] = 1
    task.aparm[10] = 1
    parse_params(task, params)
    task.go()
    
    final = grab_catalogue(uvdata.disk)
    output = compare_catalogues(initial, final)
    return AIPSUVData(output.name, output.klass, uvdata.disk, output.seq)

def split(uvdata, source, mode='both', params=None):
    # split data by source into single-source catalogue
    initial = grab_catalogue(uvdata.disk)
    
    task = AIPSTask('SPLIT')
    task.indata = uvdata
    task.sources = AIPSList([source])
    task.aparm[5] = {
        'cross': 0,
        'both': 1,
        'auto': 2
    }[mode]
    parse_params(task, params)
    task.go()

    final = grab_catalogue(uvdata.disk)
    output = compare_catalogues(initial, final)
    return AIPSUVData(output.name, output.klass, uvdata.disk, output.seq)

def fittp(uvdata, filename):
    # write catalogue to fits file
    task = AIPSTask('FITTP')
    task.indata = uvdata
    task.doall = 1
    task.dataout = os.path.realpath(filename)
    task.go()

def calib(uvdata_1, uvdata_2, calsour, params=None):
    # perform calibration based on source model
    task = AIPSTask('CALIB')
    task.indata = uvdata_1
    task.in2data = uvdata_2
    task.calsour = AIPSList(calsour)
    parse_params(task, params)
    task.go()

def tacop(uvdata_in, uvdata_out, inext, invers=0, ncount=1, params=None):
    # copy table
    task = AIPSTask('TACOP')
    task.indata = uvdata_in
    task.outdata = uvdata_out
    task.inext = inext
    task.invers = invers
    task.ncount = ncount
    parse_params(task, params)
    task.go()

def imagr(uvdata, cellsize, imsize, niter=0, params=None):
    # perform imaging
    initial = grab_catalogue(uvdata.disk)
    
    task = AIPSTask('IMAGR')
    task.indata = uvdata
    if isinstance(cellsize, float):
        task.cellsize = AIPSList([cellsize, cellsize])
    else:
        task.cellsize = AIPSList([*cellsize])
    if isinstance(imsize, int):
        task.imsize = AIPSList([imsize, imsize])
    else:
        task.imsize = AIPSList([*imsize])
    task.do3dimag = 1
    task.niter = niter
    task.dotv = -1
    parse_params(task, params)
    task.go()
    
    final = grab_catalogue(uvdata.disk)
    output = compare_catalogues(initial, final, return_multiple=True)
    return [AIPSImage(item.name, item.klass, uvdata.disk, item.seq) for item in output]

def ccmrg(image, invers=0, outvers=0):
    # merge clean components
    task = AIPSTask('CCMRG')
    task.indata = image
    task.invers = invers
    task.outvers = outvers
    task.go()
