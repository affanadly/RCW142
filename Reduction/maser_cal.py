from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from tasks import *

def maser_fring(uvdata, target, params=None): 
    # fringe fitting
    task = AIPSTask('FRING')
    task.indata = uvdata
    task.calsour = AIPSList(target)
    parse_params(task, params)
    task.go()

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Performs rate calibration using brightest maser peak.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-f', '--flagver', type=int, help='Flag table version to apply', required=True)
    ps.add_argument('-t', '--target', type=str, nargs='+', help='Target maser sources to use for fringe fitting', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('-pc', '--peak_chan', type=int, help='Peak channel in maser spectrum', metavar='CHANNEL', required=True)
    ps.add_argument('--refant', type=int, help='Reference antenna', required=True)
    ps.add_argument('--rate_int', type=float, help='Rate solution interval in minutes', metavar='SOLINT', default=1)
    ps.add_argument('--rate_sub', type=float, help='Rate solution subinterval in minutes', metavar='SOLSUB', default=10)
    ps.add_argument('--rate_win', type=int, help='Rate window in mHz', metavar='RATE', default=800)
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # load catalogue
    AIPS.userno = args.userno
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    
    # rate calibrator fringe fitting
    maser_fring(uvdata, args.target, params={
        'bchan': args.peak_chan,
        'echan': args.peak_chan,
        'docalib': 1,
        'gainuse': 4,
        'flagver': args.flagver,
        'doband': 2,
        'bpver': 1,
        'refant': args.refant,
        'solint': args.rate_int,
        'solsub': args.rate_sub,
        'aparm|5': 1,
        'aparm|6': 1,
        'aparm|7': 3,
        'aparm|9': 1,
        'dparm|2': -1,
        'dparm|3': args.rate_win
    })
    clcal(uvdata, params={
        'calsour': AIPSList(args.target),
        'sources': AIPSList(args.target),
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 5,
        'invers': 5,
        'gainver': 4,
        'gainuse': 5,
        'refant': args.refant
    })