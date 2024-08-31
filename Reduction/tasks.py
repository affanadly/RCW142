import os

from AIPSData import AIPSUVData
from AIPSTask import AIPSTask, AIPSList

from utils import *

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

def tacop(source, target, inext, invers, ncount, params=None):
    # transfer calibration solutions
    task = AIPSTask('TACOP')
    task.indata = source
    task.outdata = target
    task.inext = inext
    task.invers = invers
    task.ncount = ncount
    parse_params(task, params)
    task.go()

def splat(uvdata, mode='both', sources=None, params=None):
    initial = grab_catalogue(uvdata.disk)
    
    # split data into sources
    task = AIPSTask('SPLAT')
    task.indata = uvdata
    if sources:
        task.sources = AIPSList(sources)
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

def fittp(uvdata, output_name):
    # export data to FITS file
    task = AIPSTask('FITTP')
    task.indata = uvdata
    task.dataout = os.path.realpath(output_name)
    task.doall = 1
    task.go()