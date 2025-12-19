from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSList

from tasks import *

# ----- #

if __name__ == "__main__":
    """
    This script is the AIPS calibration pipeline for dual-beam inverse
    phase-referencing to be used on VERA data, primarily for 22 GHz
    water masers.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='VERA IPR Pipeline',
        description='''AIPS calibration pipeline for dual-beam inverse
            phase-referencing to be used on VERA data, primarily for 22 GHz 
            water masers.''',
        fromfile_prefix_chars='@'
    )
    ps.add_argument(
        'userno', type=int,
        help='AIPS user number',
        metavar='USER_NO'
    )
    ps.add_argument(
        '-f', '--files', type=str, nargs=2,
        help='Visibility file names to load (A-beam and B-beam)',
        metavar=('FILE_A', 'FILE_B'), required=True
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
        '-w', '--weak_continuum', type=str,
        help='Weak continuum source name',
        metavar='WEAK_CONTINUUM', required=True
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
        '--flag_files', type=str, nargs=2,
        help='Flag table file names', 
        metavar='FLAG_FILE', default=(None, None)
    )
    ps.add_argument(
        '--accor_solint', type=float,
        help='ACCOR solution interval in minutes',
        metavar='SOLINT', default=5
    )
    ps.add_argument(
        '--antab_files', type=str, nargs=2,
        help='ANTAB file names', 
        metavar='ANTAB_FILE', required=True
    )
    ps.add_argument(
        '--apcal_solint', type=float,
        help='APCAL solution interval in minutes',
        metavar='SOLINT', default=3
    )
    ps.add_argument(
        '--restfreq', type=float, nargs=2, 
        help='Rest frequency of spectral line (FREQ_1 + FREQ_2)', 
        metavar=('FREQ_1', 'FREQ_2'), default=(22.23E9, 5080000)
    )
    ps.add_argument(
        '--uvw_files', type=str, nargs=2,
        help='UVW correction table file names',
        metavar='UVW_FILE', required=True
    )
    ps.add_argument(
        '--refant', type=int, 
        help='Reference antenna for phase, delay, and rate calibrations', 
        metavar='REFANT', required=True
    )
    ps.add_argument(
        '--continuum_solint', type=float, 
        help='Continuum delay solution interval in minutes', 
        metavar='SOLINT', default=20
    )
    ps.add_argument(
        '--continuum_solsub', type=float,
        help='Continuum delay solution subinterval in minutes',
        metavar='SOLSUB', default=0
    )
    ps.add_argument(
        '--continuum_solwin', type=float, nargs=2, 
        help='Continuum delay and rate solution windows in ns and mHz', 
        metavar=('DELAY', 'RATE'), default=(200, 200)
    )
    ps.add_argument(
        '--db_file', type=str,
        help='Dual-beam correction file name (A to B)',
        metavar='DB_FILE', required=True
    )
    ps.add_argument(
        '--phase_ref_chan', type=int, 
        help='Phase reference channel in maser spectrum', 
        metavar='CHANNEL', required=True
    )
    ps.add_argument(
        '--maser_solint', type=float, 
        help='Maser rate solution interval in minutes', 
        metavar='SOLINT', default=0.1
    )
    ps.add_argument(
        '--maser_solsub', type=float, 
        help='Maser rate solution subinterval in minutes', 
        metavar='SOLSUB', default=0
    )
    ps.add_argument(
        '--maser_solwin', type=int, 
        help='Maser rate solution window in mHz', 
        metavar='RATE', default=120
    )
    args = ps.parse_args()
    beams = ['A', 'B']
    args.files = {beam: args.files[i] for i, beam in enumerate(beams)}
    args.flag_files = {beam: args.flag_files[i] for i, beam in enumerate(beams)}
    args.antab_files = {beam: args.antab_files[i] for i, beam in enumerate(beams)}
    args.uvw_files = {beam: args.uvw_files[i] for i, beam in enumerate(beams)}
    
    # prepare AIPS
    AIPS.userno = args.userno
    if args.log is not None:
        AIPS.log = open(args.log, 'w')
    
    # load, sort, and index visibility data
    uvdata = {
        beam: fitld(
            datain=args.files[beam],
            outdisk=args.disk,
            sources=[args.target, *args.calibrator, args.weak_continuum],
            clint=args.clint,
            params={'doconcat': 0}
        )
        for beam in beams
    }
    sorted_uvdata = {
        beam: msort(indata=uv, sort='TB') for beam, uv in uvdata.items()
    }
    for uv in uvdata.values(): uv.zap()
    uvdata = sorted_uvdata
    for beam, uv in uvdata.items(): indxr(indata=uv, solint=args.clint)

    # flag visibilities
    flagver = {}
    for beam, uv in uvdata.items():
        if args.flag_files[beam] is not None:
            tbin(intext=args.flag_files[beam], outdata=uv)
            flagver[beam] = 1
        else:
            flagver[beam] = -1
    
    # calibrate amplitudes
    for beam, uv in uvdata.items():
        accor(indata=uv, solint=args.accor_solint)
        snedt(indata=uv, invers=1, params={'flagver': flagver[beam]})
        clcal(
            indata=uv,
            snver=2, invers=2, gainver=1, gainuse=2,
            params={'interpol': '2PT'}
        )
        antab(indata=uv, calin=args.antab_files[beam])
        apcal(indata=uv, params={'solint': args.apcal_solint})
        clcal(
            indata=uv,
            snver=3, invers=3, gainver=2, gainuse=3,
            params={
                'interpol': '2PT', 
                'samptype': 'BOX', 
                'bparm|1': args.apcal_solint/60
            }
        )
        bpass(
            indata=uv,
            calsour=args.calibrator,
            params={
                'flagver': flagver[beam],
                'solint': -1,
                'bpassprm|1': 1,
            }
        )
    
    # calibrate doppler in A-beam
    tabed(
        indata=uvdata['A'],
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
        indata=uvdata['A'],
        sources=args.target,
        params={
            'optype': 'VCAL',
            'restfreq|1': args.restfreq[0],
            'restfreq|2': args.restfreq[1],
            'veltyp': 'LSR',
            'veldef': 'RADIO',
        }
    )
    uvdata['A'] = cvel(
        indata=uvdata['A'],
        sources=args.target,
        params={
            'aparm|4': 1,
            'aparm|10': 1,
        }
    )
    tabed(
        indata=uvdata['A'],
        params={
            'inext': 'AN',
            'invers': 1,
            'optype': 'KEY',
            'aparm|4': 3,
            'keyword': 'ARRNAM',
            'keystrng': 'VERA',
        }
    )
    
    # apply uvw corrections
    for beam, uv in uvdata.items():
        tbin(outdata=uv, intext=args.uvw_files[beam])
        snedt(indata=uv, invers=4, params={'dodelay': 1})
        clcal(
            indata=uv,
            snver=5, invers=5, gainver=3, gainuse=4,
            params={
                'opcode': 'CALP',
                'refant': args.refant
            }
        )
    
    # calibrate delays with continuum calibrator
    for beam, uv in uvdata.items():
        fring(
            indata=uv,
            calsour=args.calibrator,
            params={
                'docalib': 1,
                'gainuse': 4,
                'flagver': flagver[beam],
                'refant': args.refant,
                'solint': args.continuum_solint,
                'solsub': args.continuum_solsub,
                'aparm|1': 2,
                'aparm|4': -1,
                'aparm|5': 1,
                'aparm|7': 4,
                'aparm|9': 1,
                'dparm|1': 2,
                'dparm|2': args.continuum_solwin[0],
                'dparm|3': args.continuum_solwin[1],
                'dparm|5': -1,
                'dparm|8': 1,
            }
        )
        snedt(indata=uv, invers=6, params={'flagver': flagver[beam]})
        clcal(
            indata=uv,
            calsour=args.calibrator,
            snver=7, invers=7, gainver=4, gainuse=5,
            params={
                'opcode': 'CALP',
                'interpol': '2PT',
                'samptype': 'BOX',
                'smotype': 'FULL',
                'refant': args.refant,
            }
        )
    
    # average B-beam weak continuum source in frequency
    uvdata['B'] = splat(
        indata=uvdata['B'],
        sources=args.weak_continuum,
        params={
            'outname': args.weak_continuum,
            'docalib': 1,
            'gainuse': 5,
            # 'flagver': 1,
            'aparm|1': 2,
        }
    )
    
    # apply dual-beam correction (A to B)
    tbin(intext=args.db_file, outdata=uvdata['A'])
    snedt(indata=uvdata['A'], invers=8, params={'flagver': flagver['A']})
    clcal(
        indata=uvdata['A'],
        snver=9, invers=9, gainver=5, gainuse=6,
        params={
            'opcode': 'CALP',
            'interpol': 'SELF',
            'samptype': 'BOX',
            'refant': args.refant,
        }
    )
    
    # calibrate rates with target maser
    fring(
        indata=uvdata['A'],
        calsour=args.target,
        params={
            'bchan': args.phase_ref_chan,
            'echan': args.phase_ref_chan,
            'docalib': 1,
            'gainuse': 6,
            'flagver': flagver['A'],
            'refant': args.refant,
            'solint': args.maser_solint,
            'solsub': args.maser_solsub,
            'aparm|1': 2,
            'aparm|5': 0,
            'aparm|7': 3,
            'aparm|9': 1,
            'dparm|1': 2,
            'dparm|2': -1,
            'dparm|3': args.maser_solwin
        }
    )
    snedt(indata=uvdata['A'], invers=10, params={'flagver': flagver['A']})
    clcal(
        indata=uvdata['A'],
        calsour=args.target,
        snver=11, invers=11, gainver=6, gainuse=7,
        params={
            'opcode': 'CALP',
            'interpol': 'AMBG',
            'samptype': 'BOX',
            'smotype': 'FULL',
            'refant': args.refant,
        }
    )
    
    # transfer rate solution from A to B
    tacop(
        indata=uvdata['A'],
        outdata=uvdata['B'],
        inext='SN',
        invers=11,
        outvers=1,
    )
    clcal(
        indata=uvdata['B'],
        snver=1, invers=1, gainver=1, gainuse=2,
        params={
            'interpol': 'AMBG',
            'samptype': 'BOX',
            'smotype': 'FULL',
            'refant': args.refant,
        }
    )
    
    # finalize calibrations
    for beam, uv in uvdata.items():
        uv = split(
            indata=uv,
            sources=args.target if beam == 'A' else args.weak_continuum,
            params={
                'flagver': flagver[beam],
                'docalib': 1,
                'gainuse': 7 if beam == 'A' else 2,
            }
        )
    
    # close log
    if args.log is not None:
        AIPS.log.close()