from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from tasks import *

def fring(uvdata, calsour, params=None): 
    # fringe fitting
    task = AIPSTask('FRING')
    task.indata = uvdata
    task.calsour = AIPSList(calsour)
    parse_params(task, params)
    task.go()

def snsmo(uvdata, params=None):
    # smooth solution tables
    task = AIPSTask('SNSMO')
    task.indata = uvdata
    parse_params(task, params)
    task.go()

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Performs rate calibration using brightest maser peak.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-m', '--master', type=str, nargs=4, help='Master catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-f', '--flagver', type=int, help='Flag table version to apply', required=True)
    ps.add_argument('-t', '--target', type=str, nargs='+', help='Target maser sources to use for fringe fitting', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('-pc', '--peak_chan', type=int, help='Peak channel in maser spectrum', metavar='CHANNEL', required=True)
    ps.add_argument('--refant', type=int, help='Primary reference antenna', required=True)
    ps.add_argument('--search', type=int, nargs='+', help='Secondary search antennas', metavar=('ANTENNA_1', 'ANTENNA_2'), required=True)
    ps.add_argument('--rate_int', type=float, help='Rate solution interval in minutes', metavar='SOLINT', default=1)
    ps.add_argument('--rate_win', type=int, help='Rate window in MHz', metavar='RATE', default=100)
    args = ps.parse_args()
    args.master[2] = int(args.master[2])
    args.master[3] = int(args.master[3])
    
    AIPS.userno = args.userno
    
    master = AIPSUVData(args.master[0], args.master[1], args.master[3], args.master[2])
    
    fring(master, args.target, params={
        'bchan': args.peak_chan,
        'echan': args.peak_chan,
        'docalib': 1,
        'gainuse': 6,
        'flagver': args.flagver,
        'doband': 1,
        'bpver': 1,
        'refant': args.refant,
        'search': AIPSList(args.search),
        'solint': args.rate_int,
        'aparm|6': 3,
        'aparm|7': 5,
        'aparm|9': 1,
        'dparm|2': -1,
        'dparm|3': args.rate_win
    })
    snsmo(master, params={
        'samptype': 'box',
        'bparm|3': 0.5, 
        'smotype': 'VLBI',
        'invers': 7,
        'refant': args.refant
    })
    clcal(master, sources=args.target, calsour=args.target, params={
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 8,
        'invers': 8,
        'gainver': 6,
        'gainuse': 7,
        'refant': args.refant
    })
