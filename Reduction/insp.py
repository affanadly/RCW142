import os
from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSList
from AIPSData import AIPSUVData

from tasks import possm, uvplt, vplot

# ----- #

if __name__ == '__main__':
    """
    This script plots inspection data for visibility data in AIPS.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='Inspect',
        description='''Plots inspection data for visibility data in AIPS.''',
        fromfile_prefix_chars='@'
    )
    ps.add_argument(
        'userno', type=int, 
        help='User number', 
        metavar='USER_NO'
    )
    ps.add_argument(
        '-c', '--catalogue', type=str, nargs=4, 
        help='Visibility catalogue information', 
        metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True
    )
    ps.add_argument(
        '-t', '--type', type=str, 
        choices=[
            'uv_coverage', 'amp_distance', 'phase_distance', 'vis_time', 
            'auto_corr', 'cross_corr'
        ], 
        help='Type of inspection plot to generate', 
        metavar='TYPE', required=True
    )
    ps.add_argument(
        '--sources', type=str, nargs='+', 
        help='Sources to plot', 
        metavar=('SOURCE_1', 'SOURCE_2'), default=[]
    )
    ps.add_argument(
        '--time', type=int, nargs=8, 
        help='Time range to plot', 
        metavar=(
            'START_DAY', 'START_HOUR', 'START_MIN', 'START_SEC', 
            'END_DAY', 'END_HOUR', 'END_MIN', 'END_SEC'
        ), 
        default=[0, 0, 0, 0, 0, 0, 0, 0]
    )
    ps.add_argument(
        '--antenna', type=int, nargs='+', 
        help='Antennas to plot', 
        metavar=('ANTENNA_1', 'ANTENNA_2'), default=[0]
    )
    ps.add_argument(
        '--baseline', type=int, nargs='+', 
        help='Baselines to plot', 
        metavar=('BASELINE_1', 'BASELINE_2'), default=[0]
    )
    ps.add_argument(
        '--channel', type=int, nargs=2, 
        help='Channel range to plot', 
        metavar=('BCHAN', 'ECHAN'), default=[0, 0]
    )
    ps.add_argument(
        '--cal', type=int, 
        help='Calibration table to apply', 
        metavar='CAL_TABLE', default=-1
    )
    ps.add_argument(
        '--flag', type=int, 
        help='Flag table to apply', 
        metavar='FLAG_TABLE', default=-1
    )
    ps.add_argument(
        '--band', type=int, 
        help='Bandpass table to apply', 
        metavar='BAND_TABLE', default=-1
    )
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # prepare AIPS
    AIPS.userno = args.userno
    uvdata = AIPSUVData(
        args.catalogue[0], args.catalogue[1], 
        args.catalogue[3], args.catalogue[2]
    )
    
    # initialize filter and calibration parameters
    params = {
        'timerang': AIPSList(args.time),
        'antennas': AIPSList(args.antenna),
        'baseline': AIPSList(args.baseline),
        'bchan': args.channel[0],
        'echan': args.channel[1],
        'docalib': 1 if args.cal >= 0 else 0,
        'gainuse': args.cal,
        'flagver': args.flag,
        'doband': 2 if args.band >= 0 else 0,
        'bpver': args.band,
    }
    
    # plot based on type
    if args.type == 'uv_coverage':
        uvplt(
            indata=uvdata, 
            sources=args.sources,
            params=params | {
                'bparm': AIPSList([6, 7, 2, 0]),
                'dotv': 1
            }
        )
    elif args.type == 'amp_distance':
        uvplt(
            indata=uvdata, 
            sources=args.sources,
            params=params | {
                'bparm': AIPSList([0]),
                'dotv': 1
            }
        )
    elif args.type == 'phase_distance':
        uvplt(
            indata=uvdata, 
            sources=args.sources,
            params=params | {
                'bparm': AIPSList([0, 2, 0]),
                'dotv': 1
            }
        )
    elif args.type == 'vis_time':
        vplot(
            indata=uvdata, 
            sources=args.sources,
            params=params | {
                'aparm|5': 1,
                'nplots': 6,
                'dotv': 1
            }
        )
    elif args.type == 'auto_corr':
        possm(
            indata=uvdata, 
            sources=args.sources,
            params=params | {
                'aparm|1': -1,
                'aparm|8': 1,
                'nplots': 9,
                'dotv': 1
            }
        )
    elif args.type == 'cross_corr':
        possm(
            indata=uvdata, 
            sources=args.sources,
            params=params | {
                'aparm|1': -1,
                'aparm|8': 0,
                'nplots': 9,
                'dotv': 1
            }
        )
