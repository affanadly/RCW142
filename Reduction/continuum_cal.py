from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from utils import *
from tasks import *

def fring(uvdata, calsour, params=None): 
    # fringe fitting
    task = AIPSTask('FRING')
    task.indata = uvdata
    task.calsour = AIPSList(calsour)
    parse_params(task, params)
    task.go()

def phase_bpass(uvdata, calsour, params=None):
    # generate phase bandpass table
    task = AIPSTask('BPASS')
    task.indata = uvdata
    task.calsour = AIPSList(calsour)
    task.bpassprm[4] = 1
    parse_params(task, params)
    task.go()

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Performs delay calibrations using continuum sources for clock, atmospheric, and bandpass.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-m', '--master', type=str, nargs=4, help='Master catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-a', '--auxiliary', type=str, nargs=4, help='Auxiliary catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-f', '--flagver', type=int, help='Flag table version', required=True)
    ps.add_argument('--primary', type=str, nargs='+', help='Primary calibrator sources to use for clock and bandpass fringe fitting', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('--secondary', type=str, nargs='+', help='Secondary calibrator sources to use for atmospheric fringe fitting', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('--refant', type=int, help='Primary reference antenna', required=True)
    ps.add_argument('--search', type=int, nargs='+', help='Secondary search antennas', metavar=('ANTENNA_1', 'ANTENNA_2'), required=True)
    ps.add_argument('--clock_int', type=float, help='Clock delay solution interval in minutes', metavar='SOLINT', default=5)
    ps.add_argument('--clock_win', type=float, nargs=2, help='Clock delay and rate windows in ns and MHz', metavar=('DELAY', 'RATE'), default=[200, 200])
    ps.add_argument('--atmos_int', type=float, help='Atmospheric delay solution interval', metavar='SOLINT', default=5)
    ps.add_argument('--atmos_win', type=float, nargs=2, help='Atmospheric delay and rate windows in ns and MHz', metavar=('DELAY', 'RATE'), default=[100, 100])
    ps.add_argument('--bpass_int', type=float, help='Bandpass phase solution interval in minutes', metavar='SOLINT', default=1)
    args = ps.parse_args()
    args.master[2] = int(args.master[2])
    args.master[3] = int(args.master[3])
    args.auxiliary[2] = int(args.auxiliary[2])
    args.auxiliary[3] = int(args.auxiliary[3])
    
    AIPS.userno = args.userno
    
    master = AIPSUVData(args.master[0], args.master[1], args.master[3], args.master[2])
    auxiliary = AIPSUVData(args.auxiliary[0], args.auxiliary[1], args.auxiliary[3], args.auxiliary[2])
    
    # clock delay calibration
    fring(auxiliary, args.primary, params={
        'bchan': 2,
        'echan': 63,
        'docalib': 1,
        'gainuse': 3,
        'doband': 2,
        'bpver': 1,
        'flagver': args.flagver,
        'refant': args.refant,
        'search': AIPSList(args.search),
        'solint': args.clock_int,
        'aparm|6': 3,
        'aparm|7': 10,
        'aparm|9': 1,
        'dparm|2': args.clock_win[0],
        'dparm|3': args.clock_win[1],
        'dparm|8': 1
    })
    clcal(auxiliary, params={
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 4,
        'invers': 4,
        'gainver': 3,
        'gainuse': 4,
        'refant': args.refant
    })
    
    # atmospheric delay correction
    fring(auxiliary, args.secondary, params={
        'bchan': 2,
        'echan': 63,
        'docalib': 1,
        'gainuse': 4,
        'doband': 2,
        'bpver': 1,
        'flagver': args.flagver,
        'refant': args.refant,
        'search': AIPSList(args.search),
        'solint': args.atmos_int,
        'aparm|6': 3,
        'aparm|7': 5,
        'aparm|9': 1,
        'dparm|2': args.atmos_win[0],
        'dparm|3': args.atmos_win[1],
        'dparm|8': 1
    })
    
    # pre-bandpass phase calibration
    fring(auxiliary, args.primary, params={
        'bchan': 2,
        'echan': 63,
        'docalib': 1,
        'gainuse': 3,
        'doband': 2,
        'bpver': 1,
        'flagver': args.flagver,
        'refant': args.refant,
        'search': AIPSList(args.search),
        'solint': args.bpass_int,
        'aparm|6': 3,
        'aparm|7': 10,
        'aparm|9': 1,
        'dparm|2': 200,
        'dparm|3': 200
    })
    
    # transfer phase and delay solutions
    tacop(auxiliary, master, inext='SN', invers=4, ncount=3)
    clcal(master, params={
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 6,
        'invers': 6,
        'gainver': 3,
        'gainuse': 4,
        'refant': args.refant
    })
    clcal(master, params={
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 4,
        'invers': 4,
        'gainver': 3,
        'gainuse': 5,
        'refant': args.refant
    })
    clcal(master, params={
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 5,
        'invers': 5,
        'gainver': 5,
        'gainuse': 6,
        'refant': args.refant
    })
    
    # bandpass phase calibration
    phase_bpass(master, args.primary, params={
        'docalib': 1,
        'gainuse': 4,
        'doband': 2,
        'bpver': 1,
        'flagver': args.flagver,
        'solint': -1,
        'soltype': 'L1R',
        'refant': args.refant
    })
    
    # finalizing calibrations
    master_splat = splat(master, mode='all', params={
        'doband': 2,
        'bpver': 1
    })
    tacop(master, master_splat, inext='BP', invers=2, ncount=1)
