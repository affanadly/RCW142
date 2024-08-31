from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from utils import *
from tasks import *

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Performs rate calibration using brightest maser peak.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-t', '--target', type=str, nargs='+', help='Target maser sources', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('-f', '--flagver', type=int, help='Flag table version to apply', metavar='FG', default=-1)
    ps.add_argument('-g', '--gainuse', type=int, help='Gain table version to apply', metavar='CL', default=-1)
    ps.add_argument('-b', '--bpver', type=int, help='Bandpass table version to apply', metavar='BP', default=-1)
    ps.add_argument('--output', type=str, help='Output filename', default='')
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # load catalogue
    AIPS.userno = args.userno
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    
    # splat out final data
    uvdata_out = splat(uvdata, mode='both', sources=args.target, params={
        'outname': args.target[0],
        'docalib': 1,
        'gainuse': args.gainuse,
        'doband': 2,
        'bpver': args.bpver,
        'flagver': args.flagver
    })
    if args.output:
        fittp(uvdata_out, args.output)