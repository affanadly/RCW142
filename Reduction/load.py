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
    task.digicor = -1
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
    ps = ArgumentParser(description='Loads, sorts, and indexes visibility data from FITS files into AIPS.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-m', '--master', type=str, help='Master visibility file name to load', metavar='MASTER_FILE', required=True)
    ps.add_argument('-a', '--auxiliary', type=str, help='Auxiliary visibility file name to load', metavar='AUXILIARY_FILE', required=True)
    ps.add_argument('-s', '--sources', type=str, nargs='+', help='Sources to read in files', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('-d', '--disk', type=int, help='AIPS disk number to load into', required=True)
    ps.add_argument('-cl', '--clint', type=float, help='Integration time in minutes', required=True)
    args = ps.parse_args()
    
    AIPS.userno = args.userno
    
    # load master file
    master = fitld(args.master, args.disk, args.clint, args.sources, 
                   params={'outname': 'MASTR'})
    sorted_master = msort(master, params={'sort': 'TB'})
    master.zap()
    indxr(sorted_master, args.clint)
    
    # load auxiliary file
    auxiliary = fitld(args.auxiliary, args.disk, args.clint, args.sources, 
                      {'outname': 'AUXIL', 'bif': 1, 'eif': 1})
    sorted_auxiliary = msort(auxiliary, params={'sort': 'TB'})
    auxiliary.zap()
    indxr(sorted_auxiliary, args.clint)
