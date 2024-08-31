import os
from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData
from AIPSTV import AIPSTV

from utils import *
from tasks import *

def accor(uvdata, solint, params=None):
    # correct sampler errors
    task = AIPSTask('ACCOR')
    task.indata = uvdata
    task.solint = solint
    parse_params(task, params)
    task.go()

def snedt(uvdata, inext='SN', invers=0, solint=None, params=None):
    tv = AIPSTV()
    tv.start()
    
    # edit anomalous solutions
    task = AIPSTask('SNEDT')
    task.indata = uvdata
    task.inext = inext
    task.invers = invers
    if solint:
        task.solint = solint
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

def apcal(uvdata, solint=None, params=None):
    # generate amplitude solutions
    task = AIPSTask('APCAL')
    task.indata = uvdata
    if solint:
        task.solint = solint
    parse_params(task, params)
    task.go()

def amp_bpass(uvdata, calsour, params=None):
    # generate amplitude bandpass table
    task = AIPSTask('BPASS')
    task.indata = uvdata
    task.calsour = AIPSList(calsour)
    task.bpassprm[1] = 1
    task.bpassprm[10] = 1
    parse_params(task, params)
    task.go()

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Performs amplitude calibration (ACCOR, ANTAB, and BPASS).')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-f', '--flagver', type=int, help='Flag table version to apply', default=-1)
    ps.add_argument('--accor_solint', type=float, help='ACCOR solution interval in minutes', required=True)
    ps.add_argument('--antab_file', type=str, help='ANTAB file to apply', required=True)
    ps.add_argument('--apcal_solint', type=float, help='APCAL solution interval in minutes', default=0)
    ps.add_argument('--bpass_sources', type=str, nargs='+', help='Sources to use for BPASS', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # load catalogue
    AIPS.userno = args.userno
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    
    # calibrate sampler thresholds
    accor(uvdata, args.accor_solint, params={'flagver': args.flagver})
    snedt(uvdata, inext='SN', invers=1, solint=args.accor_solint, params={'flagver': args.flagver})
    clcal(uvdata, params={
        'opcode': 'CALI',
        'interpol': 'SELF',
        'smotype': 'AMPL',
        'snver': 2, 
        'invers': 2,
        'gainver': 1,
        'gainuse': 2,
        'refant': -1
    })
    
    # calibrate antenna gain and system temperature
    antab(uvdata, args.antab_file)
    apcal(uvdata)
    clcal(uvdata, params={
        'opcode': 'CALI',
        'interpol': '2PT', 
        'smotype': 'AMPL',
        'snver': 3,
        'invers': 3,
        'gainver': 2,
        'gainuse': 3,
        'refant': -1
    })
    
    # calibrate amplitude bandpass
    amp_bpass(uvdata, args.bpass_sources, params={
        'docalib': 1,
        'gainuse': 3,
        'flagver': args.flagver,
        'solint': 0,
        'soltype': 'L1R',
    })
