import os
from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from utils import *
from tasks import *
from load import fitld
from amp_cal import snedt

def selfcal_calib(peak_data, selfcal_data, params=None):
    # apply self-calibration solution to peak data
    task = AIPSTask('CALIB')
    task.indata = peak_data
    task.in2data = selfcal_data
    parse_params(task, params)
    task.go()

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Loads a self-calibrated FITS file into AIPS and applying solutions to other catalogues.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-i', '--input', type=str, help='Input FITS file name', metavar='INPUT_FILE', required=True)
    ps.add_argument('-p', '--pchan', type=str, nargs=4, help='Peak channel catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-m', '--master', type=str, nargs=4, help='Master catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-t', '--target', type=str, help='Target maser source', metavar='SOURCE', required=True)
    ps.add_argument('-cl', '--clint', type=float, help='Integration time in minutes', required=True)
    ps.add_argument('--refant', type=int, help='Primary reference antenna', required=True)
    ps.add_argument('--calib_solint', type=float, help='Self-calibration solution interval in minutes', default=1)
    ps.add_argument('--calib_solsub', type=float, help='Self-calibration solution subinterval in minutes', default=1)
    args = ps.parse_args()
    args.pchan[2] = int(args.pchan[2])
    args.pchan[3] = int(args.pchan[3])
    args.master[2] = int(args.master[2])
    args.master[3] = int(args.master[3])
    
    AIPS.userno = args.userno
    
    master_pchan = AIPSUVData(args.pchan[0], args.pchan[1], args.pchan[3], args.pchan[2])
    master = AIPSUVData(args.master[0], args.master[1], args.master[3], args.master[2])
    
    master_selfcal = fitld(args.input, master_pchan.disk, args.clint, [args.target])
    selfcal_calib(master_pchan, master_selfcal, params={
        'calsour': AIPSList([args.target]),
        'cmethod': 'DFT',
        'cmodel': 'COMP',
        'doapply': -1,
        'refant': args.refant,
        'solint': args.calib_solint,
        'solsub': args.calib_solsub,
        'aparm|1': 4,
        'aparm|7': 3,
        'soltype': 'L1R',
        'solmode': 'A&P'
    })
    snedt(master_pchan, inext='SN', invers=1, solint=args.clint, params={'dodelay': 1})
    tacop(master_pchan, master, inext='SN', invers=2, ncount=1)
    clcal(master, sources=[args.target], calsour=[args.target], params={
        'opcode': 'CALI',
        'interpol': 'SIMP',
        'smotype': 'VLBI',
        'snver': 7,
        'invers': 7,
        'gainver': 7,
        'gainuse': 8,
        'refant': args.refant
    })
