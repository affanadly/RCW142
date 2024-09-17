import os
import yaml
from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSList

from tasks import fitld, msort, indxr, uvflg, clcal, accor, snedt, antab, apcal, bpass, fring, tabed_key, cvel_doppler, set_velocity, split

# To-Do List:
# - show visibilities after loading, allow user to create flag file OR automatically flag visibilities
# - automatically determine LSR channel
# - automatically determine peak maser channel
# - handle multiple target sources
# - handle self-calibration option

# -------------------- #

if __name__ == '__main__':
    # parse arguments
    ps = ArgumentParser(description='AIPS calibration pipeline for KaVA Star Formation LP data.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    
    io = ps.add_argument_group('i/o', description='Input/Output parameters')
    io.add_argument('-f', '--file', type=str, help='Visibility file name to load', metavar='FILE', required=True)
    io.add_argument('-t', '--target', type=str, help='Target maser source name', metavar='SOURCE', required=True)
    io.add_argument('-c', '--calibrator', type=str, nargs='+', help='Continuum calibrator source name(s)', metavar=('CALIBRATOR_1', 'CALIBRATOR_2'), required=True)
    io.add_argument('-d', '--disk', type=int, help='AIPS disk number to load into', metavar='DISK', default=1)
    io.add_argument('-i', '--clint', type=float, help='Integration time in minutes', metavar='CLINT', default=0.0273)

    cali = ps.add_argument_group('calibration', description='Calibration parameters')
    cali.add_argument('--flag_file', type=str, help='Flag table file name', metavar='FLAG_FILE', default=None)
    cali.add_argument('--antab_file', type=str, help='ANTAB file name', metavar='ANTAB_FILE', required=True)
    cali.add_argument('--refant', type=int, help='Reference antenna for phase, delay, and rate calibrations', metavar='REFANT', required=True)
    cali.add_argument('--continuum_solint', type=float, help='Continuum delay solution interval in minutes', metavar='SOLINT', default=10)
    cali.add_argument('--continuum_solwin', type=float, nargs=2, help='Continuum delay and rate solution windows in ns and mHz', metavar=('DELAY', 'RATE'), default=[120, 120])
    cali.add_argument('--restfreq', type=float, nargs=2, help='Rest frequency of spectral line (FREQ_1 + FREQ_2)', metavar=('FREQ_1', 'FREQ_2'), default=(22.23E9, 5080000))
    cali.add_argument('--sysvel', type=float, help='Systemic velocity of source in km/s', metavar='VELOCITY', required=True)
    cali.add_argument('--lsr_chan', type=int, help='Channel number for LSR velocity', metavar='CHANNEL', required=True)
    cali.add_argument('--peak_chan', type=int, help='Peak channel in maser spectrum', metavar='CHANNEL', required=True)
    cali.add_argument('--maser_solint', type=float, help='Maser rate solution interval in minutes', metavar='SOLINT', default=1)
    cali.add_argument('--maser_solsub', type=float, help='Maser rate solution subinterval in minutes', metavar='SOLSUB', default=10)
    cali.add_argument('--maser_solwin', type=int, help='Maser rate solution window in mHz', metavar='RATE', default=800)
    
    args = ps.parse_args()
    
    # prepare AIPS
    AIPS.userno = args.userno
    
    # load, sort, and index visibility data
    uvdata = fitld(args.file, args.disk, args.clint, [args.target, *args.calibrator], params={
        'douvcomp': 1,
        'doconcat': -1,
        'digicor': -1,
        'wtthresh': 0.8
    })
    sorted_uvdata = msort(uvdata, params={'sort': 'TB'})
    uvdata.zap()
    uvdata = sorted_uvdata
    indxr(uvdata, args.clint)
    
    # flag visibilities
    if args.flag_file is not None:
        with open(args.flag_file, 'r') as file:
            flags = list(yaml.safe_load_all(file))
        
        for flag in flags:
            uvflg(uvdata, outfgver=1, params={
                key: AIPSList(value)
                if type(value) == list
                else value
                for key, value in flag.items()
            })
    
    # calibrate amplitudes
    accor(uvdata, params={
        'flagver': 1 if args.flag_file is not None else -1,
        'solint': args.clint
    })
    snedt(uvdata, invers=1, params={'flagver': 1 if args.flag_file is not None else -1})
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
    antab(uvdata, args.antab_file)
    apcal(uvdata)
    clcal(uvdata, params={
        'opcode': 'CALI',
        'interpol': 'SELF',
        'smotype': 'AMPL',
        'snver': 3, 
        'invers': 3,
        'gainver': 2,
        'gainuse': 3,
        'refant': -1
    })
    bpass(uvdata, args.calibrator, params={
        'docalib': 1,
        'gainuse': 3,
        'flagver': 1 if args.flag_file is not None else -1,
        'solint': 0,
        'soltype': 'L1R',
    })
    
    # calibrate delay with continuum calibrator
    fring(uvdata, args.calibrator, params={
        'bchan': 1 + 50,
        'echan': 1024 - 50,
        'docalib': 1,
        'gainuse': 3,
        'flagver': 1 if args.flag_file is not None else -1,
        'refant': args.refant,
        'solint': args.continuum_solint,
        'aparm|5': 1,
        'aparm|7': 3,
        'dparm|2': args.continuum_solwin[0],
        'dparm|3': args.continuum_solwin[1],
        'dparm|8': 1
    })
    clcal(uvdata, params={
        'calsour': AIPSList(args.calibrator),
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 4,
        'invers': 4,
        'gainver': 3,
        'gainuse': 4,
        'refant': args.refant
    })
    
    # calibrate doppler
    tabed_key(uvdata, inext='AN', invers=1, key='ARRNAM', value='VLBA')
    set_velocity(uvdata, args.restfreq, args.target, args.sysvel, args.lsr_chan)
    uvdata_cvel = cvel_doppler(uvdata, [args.target], params={
        'docalib': 1,
        'gainuse': 5,
    })
    tabed_key(uvdata, inext='AN', invers=1, key='ARRNAM', value='KVN')
    tabed_key(uvdata_cvel, inext='AN', invers=1, key='ARRNAM', value='KVN')
    uvdata = uvdata_cvel
    
    # calibrate rate with peak maser emission
    fring(uvdata, [args.target], params={
        'bchan': args.peak_chan,
        'echan': args.peak_chan,
        'docalib': 1,
        'gainuse': 4,
        'flagver': 1 if args.flag_file is not None else -1,
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
    })
    clcal(uvdata, params={
        'calsour': AIPSList([args.target]),
        'sources': AIPSList([args.target]),
        'opcode': 'CALI',
        'interpol': 'AMBG',
        'smotype': 'VLBI',
        'snver': 5,
        'invers': 5,
        'gainver': 4,
        'gainuse': 5,
        'refant': args.refant
    })
    
    # finalize reduction
    uvdata_final = split(uvdata, args.target, params={
        'flagver': 1 if args.flag_file is not None else -1,
        'docalib': 1,
        'gainuse': 5,
        'doband': 2,
        'bpver': 1
    })
