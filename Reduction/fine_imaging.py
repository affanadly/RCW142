from argparse import ArgumentParser

from astropy.table import Table

from AIPS import AIPS
from AIPSData import AIPSUVData

from tasks import imagr, fittp
from wizardry import switch_spectral

# ----- #

if __name__ == '__main__':
    """
    This script performs fine imaging for KaVA Star Formation LP data.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='Fine Imaging',
        description='''Fine imaging for KaVA Star Formation LP data.''',
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
        '--field', type=str, 
        help='Field file', 
        metavar='FIELD', required=True
    )
    ps.add_argument(
        '--niter', type=int, 
        help='Number of iterations', 
        default=500
    )
    ps.add_argument(
        '--output', type=str, 
        help='Output prefix for all images', 
        metavar='OUTPUT', default='./'
    )
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # prepare AIPS
    AIPS.userno = args.userno
    
    # load visibility data and fields
    uvdata = AIPSUVData(
        args.catalogue[0], args.catalogue[1], 
        args.catalogue[3], args.catalogue[2]
    )
    fields = Table.read(args.field, format='ascii.commented_header')
    
    # perform imaging
    images = []
    for field in fields:
        _, image = imagr(
            indata=uvdata,
            cellsize=float(field['cellsize']),
            imsize=int(field['imsize']),
            niter=args.niter,
            params={
                'bchan': int(field['bchan']),
                'echan': int(field['echan']),
                'do3dimag': 1,
                'rashift|1': float(field['rashift']),
                'decshift|1': float(field['decshift']),
                'dotv': -1
            }
        )
        switch_spectral(image)
        fittp(
            indata=image, 
            dataout=f'{args.output}fine{field["index"]:03}.fits'
        )