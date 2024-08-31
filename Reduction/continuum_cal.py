from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from utils import *
from tasks import *

def continuum_fring(uvdata, calsour, params=None): 
    # fringe fitting
    task = AIPSTask('FRING')
    task.indata = uvdata
    task.calsour = AIPSList(calsour)
    parse_params(task, params)
    task.go()

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Performs delay calibrations using continuum sources.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-f', '--flagver', type=int, help='Flag table version', default=-1)
    ps.add_argument('--primary', type=str, nargs='+', help='Primary calibrator sources to use for fringe fitting', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('--refant', type=int, help='Reference antenna', required=True)
    ps.add_argument('--clock_int', type=float, help='Clock delay solution interval in minutes', metavar='SOLINT', default=10)
    ps.add_argument('--clock_win', type=float, nargs=2, help='Clock delay and rate windows in ns and mHz', metavar=('DELAY', 'RATE'), default=[120, 120])
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # load catalogue
    AIPS.userno = args.userno
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    
    # continuum calibrator fringe fitting
    continuum_fring(uvdata, args.primary, params={
        'bchan': 1+50,
        'echan': 1024-50,
        'docalib': 1,
        'gainuse': 3,
        'flagver': args.flagver,
        'refant': args.refant,
        'solint': args.clock_int,
        'aparm|5': 1,
        'aparm|7': 3,
        'dparm|2': args.clock_win[0],
        'dparm|3': args.clock_win[1],
        'dparm|8': 1
    })
    clcal(uvdata, params={
        'calsour': AIPSList(args.primary),
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 4,
        'invers': 4,
        'gainver': 3,
        'gainuse': 4,
        'refant': args.refant
    })
