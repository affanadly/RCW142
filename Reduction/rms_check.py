from argparse import ArgumentParser

import numpy as np

from AIPS import AIPS
from AIPSData import AIPSUVData

from tasks import imagr
from wizardry import grab_im

# ----- #

if __name__ == '__main__':
    """
    This script calculates the RMS noise in a line-free channel image.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='RMS Check',
        description='Calculates RMS noise for KaVA Star Formation LP data.',
        fromfile_prefix_chars='@'
    )
    ps.add_argument(
        'userno', type=int,
        help='AIPS user number',
        metavar='USER_NO'
    )
    ps.add_argument(
        '-c', '--catalogue', type=str, nargs=4, 
        help='Visibility catalogue information', 
        metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True
    )
    ps.add_argument(
        '--channel', type=int, 
        help='Line free channel', 
        metavar='CHAN', required=True
    )
    ps.add_argument(
        '--cellsize', type=float, 
        help='Cell size in arcseconds', 
        metavar='CELLSIZE', default=1e-3
    )
    ps.add_argument(
        '--imsize', type=int, 
        help='Image size in pixels', 
        metavar='IMSIZE', default=8192
    )
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # prepare AIPS
    AIPS.userno = args.userno
    
    # load visibility data
    uvdata = AIPSUVData(
        args.catalogue[0], args.catalogue[1], 
        args.catalogue[3], args.catalogue[2]
    )
    
    # perform imaging
    images = imagr(
        indata=uvdata, 
        cellsize=args.cellsize, 
        imsize=args.imsize, 
        params={
            'bchan': args.channel,
            'echan': args.channel,
            'do3dimag': 1,
            'dotv': -1
        }
    )
    rms = np.std(grab_im(images[1]).flatten())
    for image in images:
        image.zap()
    print(f'RMS: {rms} Jy/beam')
