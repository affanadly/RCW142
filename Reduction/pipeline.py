from argparse import ArgumentParser
import yaml

from AIPS import AIPS
from AIPSTask import AIPSList

from tasks import *

# ----- #

if __name__ == '__main__':
    """
    This script is the AIPS calibration pipeline for KaVA Star Formation
    LP data, primarily for 22 GHz water masers.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='KaVA Pipeline',
        description='''AIPS calibration pipeline for KaVA Star Formation
            LP data.''',
        fromfile_prefix_chars='@'
    )
    ps.add_argument(
        'userno', type=int, 
        help='AIPS user number', 
        metavar='USER_NO'
    )
    ps.add_argument(
        '-f', '--file', type=str, 
        help='Visibility file name to load', 
        metavar='FILE', required=True
    )
    ps.add_argument(
        '-t', '--target', type=str, 
        help='Target maser source name', 
        metavar='SOURCE', required=True
    )
    ps.add_argument(
        '-c', '--calibrator', type=str, nargs='+', 
        help='Continuum calibrator source name(s)', 
        metavar=('CALIBRATOR_1', 'CALIBRATOR_2'), required=True
    )
    ps.add_argument(
        '-d', '--disk', type=int, 
        help='AIPS disk number to load into', 
        metavar='DISK', default=1
    )
    ps.add_argument(
        '-i', '--clint', type=float, 
        help='Integration time in minutes', 
        metavar='CLINT', default=0.0273
    )
    ps.add_argument(
        '--log', type=str, 
        help='Log file name', 
        metavar='LOG', default=None
    )
    ps.add_argument(
        '--flag_file', type=str, 
        help='Flag table file name', 
        metavar='FLAG_FILE', default=None
    )
    ps.add_argument(
        '--antab_file', type=str, 
        help='ANTAB file name', 
        metavar='ANTAB_FILE', required=True
    )
    ps.add_argument(
        '--refant', type=int, 
        help='Reference antenna for phase, delay, and rate calibrations', 
        metavar='REFANT', required=True
    )
    ps.add_argument(
        '--continuum_solint', type=float, 
        help='Continuum delay solution interval in minutes', 
        metavar='SOLINT', default=10
    )
    ps.add_argument(
        '--continuum_solwin', type=float, nargs=2, 
        help='Continuum delay and rate solution windows in ns and mHz', 
        metavar=('DELAY', 'RATE'), default=(120, 120)
    )
    ps.add_argument(
        '--restfreq', type=float, nargs=2, 
        help='Rest frequency of spectral line (FREQ_1 + FREQ_2)', 
        metavar=('FREQ_1', 'FREQ_2'), default=(22.23E9, 5080000)
    )
    ps.add_argument(
        '--phase_ref_chan', type=int, 
        help='Phase reference channel in maser spectrum', 
        metavar='CHANNEL', required=True
    )
    ps.add_argument(
        '--maser_solint', type=float, 
        help='Maser rate solution interval in minutes', 
        metavar='SOLINT', default=1
    )
    ps.add_argument(
        '--maser_solsub', type=float, 
        help='Maser rate solution subinterval in minutes', 
        metavar='SOLSUB', default=10
    )
    ps.add_argument(
        '--maser_solwin', type=int, 
        help='Maser rate solution window in mHz', 
        metavar='RATE', default=800
    )
    args = ps.parse_args()
    
    # prepare AIPS
    AIPS.userno = args.userno
    if args.log is not None:
        AIPS.log = open(args.log, 'w')
    
    # load, sort, and index visibility data
    uvdata = fitld(
        datain=args.file,
        outdisk=args.disk,
        sources=[args.target, *args.calibrator],
        clint=args.clint,
        params={
            'douvcomp': 1,
            'doconcat': -1,
            'digicor': -1,
            'wtthresh': 0.8,
        }
    )
    sorted_uvdata = msort(indata=uvdata, sort='TB')
    uvdata.zap()
    uvdata = sorted_uvdata
    indxr(indata=uvdata, solint=args.clint)
    
    # flag visibilities
    if args.flag_file is not None:
        with open(args.flag_file, 'r') as file:
            flags = list(yaml.safe_load_all(file))
        
        for flag in flags:
            uvflg(
                indata=uvdata, 
                outfgver=1, 
                params={
                    key: AIPSList(value)
                    if type(value) == list
                    else value
                    for key, value in flag.items()
                }
            )
        flagver = 1
    else:
        flagver = -1
    
    # calibrate amplitudes
    accor(indata=uvdata, solint=args.clint)
    snedt(indata=uvdata, invers=1, params={'flagver': flagver})
    clcal(
        indata=uvdata,
        snver=2, invers=2, gainver=1, gainuse=2,
        params={
            'opcode': 'CALI',
            'interpol': 'SELF',
            'smotype': 'AMPL',
        }
    )
    antab(indata=uvdata, calin=args.antab_file)
    apcal(indata=uvdata)
    clcal(
        indata=uvdata,
        snver=3, invers=3, gainver=2, gainuse=3,
        params={
            'opcode': 'CALI',
            'interpol': 'SELF',
            'smotype': 'AMPL',
        }
    )
    bpass(
        indata=uvdata,
        calsour=args.calibrator,
        params={
            'docalib': 1,
            'gainuse': 3,
            'flagver': flagver,
            'solint': 0,
            'soltype': 'L1R',
            'bpassprm|1': 1,
            'bpassprm|10': 1,
        }
    )
    
    # calibrate delay with continuum calibrator
    fring(
        indata=uvdata,
        calsour=args.calibrator,
        params={
            'bchan': 1 + 50,
            'echan': 1024 - 50,
            'docalib': 1,
            'gainuse': 3,
            'flagver': flagver,
            'refant': args.refant,
            'solint': args.continuum_solint,
            'aparm|5': 1,
            'aparm|7': 3,
            'dparm|2': args.continuum_solwin[0],
            'dparm|3': args.continuum_solwin[1],
            'dparm|8': 1,
        }
    )
    clcal(
        indata=uvdata,
        calsour=args.calibrator,
        snver=4, invers=4, gainver=3, gainuse=4,
        params={
            'opcode': 'CALI',
            'interpol': 'AMBG',
            'smotype': 'VLBI',
            'refant': args.refant,
        }
    )
    
    # calibrate doppler
    tabed(
        indata=uvdata,
        params={
            'inext': 'AN',
            'invers': 1,
            'optype': 'KEY',
            'aparm|4': 3,
            'keyword': 'ARRNAM',
            'keystrng': 'VLBA',
        }
    )
    setjy(
        indata=uvdata,
        sources=args.target,
        params={
            'optype': 'VCAL',
            'restfreq|1': args.restfreq[0],
            'restfreq|2': args.restfreq[1],
            'veltyp': 'LSR',
            'veldef': 'RADIO',
        }
    )
    uvdata_cvel = cvel(
        indata=uvdata,
        sources=args.target,
        params={
            'aparm|4': 1,
            'aparm|10': 1,
        }
    )
    tabed(
        indata=uvdata,
        params={
            'inext': 'AN',
            'invers': 1,
            'optype': 'KEY',
            'aparm|4': 3,
            'keyword': 'ARRNAM',
            'keystrng': 'KVN',
        }
    )
    tabed(
        indata=uvdata_cvel,
        params={
            'inext': 'AN',
            'invers': 1,
            'optype': 'KEY',
            'aparm|4': 3,
            'keyword': 'ARRNAM',
            'keystrng': 'KVN',
        }
    )
    uvdata = uvdata_cvel

    # calibrate rate with phase reference channel
    fring(
        indata=uvdata,
        calsour=[args.target],
        params={
            'bchan': args.phase_ref_chan,
            'echan': args.phase_ref_chan,
            'docalib': 1,
            'gainuse': 4,
            'flagver': flagver,
            'doband': 2,
            'bpver': 1,
            'refant': args.refant,
            'solint': args.maser_solint,
            'solsub': args.maser_solsub,
            'aparm|5': 1,
            'aparm|6': 1,
            'aparm|7': 3,
            'aparm|9': 1,
            'dparm|2': -1,
            'dparm|3': args.maser_solwin
        }
    )
    clcal(
        indata=uvdata,
        sources=args.target,
        calsour=args.target,
        snver=5, invers=5, gainver=4, gainuse=5,
        params={
            'opcode': 'CALI',
            'interpol': 'AMBG',
            'smotype': 'VLBI',
            'refant': args.refant,
        }
    )
    
    # finalize reduction
    uvdata_final = split(
        indata=uvdata,
        sources=args.target,
        mode='both',
        params={
            'flagver': flagver,
            'docalib': 1,
            'gainuse': 5,
            'doband': 2,
            'bpver': 1
        }
    )
    
    # close log
    if args.log is not None:
        AIPS.log.close()
