import os
from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from utils import *

def fitld(filename, disk, clint, sources, params=None):
    initial = grab_catalogue(disk)
    
    # load fits file
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
    initial = grab_catalogue(uvdata.disk)
    
    # sort visibilities
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

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Loads, sorts, and indexes visibility data from a FITS file into AIPS.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-f', '--file', type=str, help='Visibility file name to load', metavar='FILE', required=True)
    ps.add_argument('-s', '--sources', type=str, nargs='+', help='Sources to read in file', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('-d', '--disk', type=int, help='AIPS disk number to load into', required=True)
    ps.add_argument('-c', '--clint', type=float, help='Integration time in minutes', required=True)
    args = ps.parse_args()
    
    AIPS.userno = args.userno
    
    # load file, sort, and index
    uvdata = fitld(args.file, args.disk, args.clint, args.sources, 
                   params={
                       'douvcomp': 1,
                       'doconcat': -1,
                       'digicor': -1,
                       'wtthresh': 0.8
                   }
                )
    sorted_uvdata = msort(uvdata, params={'sort': 'TB'})
    uvdata.zap()
    indxr(sorted_uvdata, args.clint)