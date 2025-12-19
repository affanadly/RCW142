from argparse import ArgumentParser

from astropy import units as u
from astropy.table import vstack
import numpy as np

from AIPS import AIPS
from AIPSData import AIPSUVData

from tasks import imagr, ccmrg
from wizardry import switch_spectral, grab_table, grab_wcs

# ----- #

if __name__ == '__main__':
    """
    This script performs initial coarse wide-field imaging for KaVA Star 
    Formation LP data.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='Coarse Imaging',
        description='''Initial coarse wide-field imaging for KaVA Star 
            Formation LP data.''',
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
        '--channel', type=int, nargs=2, 
        help='Channel range to image', 
        metavar=('BCHAN', 'ECHAN'), default=[0, 0]
    )
    ps.add_argument(
        '--nchav', type=int, 
        help='Number of channels to average', 
        metavar='NCHAV', default=2
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
    ps.add_argument(
        '--niter', type=int, 
        help='Number of iterations for cleaning', 
        metavar='NITER', default=500
    )
    ps.add_argument(
        '--output', type=str, 
        help='Output clean component table file name',
        metavar='OUTPUT',
        default='coarse_imaging.fits'
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
    _, image = imagr(
        indata=uvdata, 
        cellsize=args.cellsize, 
        imsize=args.imsize, 
        niter=args.niter, 
        params={
            'bchan': args.channel[0],
            'echan': args.channel[1],
            'nchav': args.nchav,
            'chinc': args.nchav,
            'do3dimag': 1,
            'dotv': -1
        }
    )
    for chan in range(
        int((args.channel[1] - args.channel[0] + 1) / args.nchav)
    ):
        ccmrg(
            indata=image, 
            params={
                'invers': chan + 1,
                'outvers': chan + 1,
            }
        )
    switch_spectral(image)
    
    # grab clean components (before the first negative flux)
    wcs = grab_wcs(image)
    ccs = []
    for chan in range(
        int((args.channel[1] - args.channel[0] + 1) / args.nchav)
    ):
        cc = grab_table(
            image, 'CC', table_index=chan + 1, ignore=['_status']
        )
        cc['flux'].unit = u.Jy
        cc['deltax'] *= 3600
        cc['deltay'] *= 3600
        cc['deltax'].unit = u.arcsec
        cc['deltay'].unit = u.arcsec
        cc['bchan'] = args.channel[0] + args.nchav * chan
        cc['echan'] = args.channel[0] + args.nchav * chan + args.nchav - 1
        cc['velocity'] = wcs.spectral.pixel_to_world(chan)
        cc['velocity'] = cc['velocity'].to(u.km / u.s)
        cc = cc[:np.where(cc['flux'] < 0)[0][0]]
        ccs.append(cc)
    ccs = vstack(ccs)
    ccs.write(args.output, format='fits', overwrite=True)
