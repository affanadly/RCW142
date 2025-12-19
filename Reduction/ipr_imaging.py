from argparse import ArgumentParser
from astropy.io import fits
from astropy.table import QTable
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import numpy as np

from AIPS import AIPS
from AIPSTask import AIPSList

from tasks import *
from wizardry import grab_im

# ----- #

if __name__ == "__main__":
    """
    This script is the AIPS pipeline for imaging the results of
    dual-beam inverse phase-referencing (IPR) calibration on VERA data,
    primarily for 22 GHz water masers. The script allows for iterative
    imaging to search for the weak continuum source (which was
    inversely phase-referenced to a maser). 
    """
    # parse arguments
    ps = ArgumentParser(
        prog='VERA IPR Imaging',
        description='''AIPS imaging pipeline for dual-beam inverse
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
        '-w', '--weak_continuum', type=str, nargs=4,
        help='Weak continuum visibility catalogue information',
        metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True
    )
    ps.add_argument(
        '-i', '--imaging_params', type=str, nargs=2,
        help='Initial imaging parameters: cellsize (arcsec), imsize (pixels)',
        metavar=('CELLSIZE', 'IMSIZE'), default=(0.001, 4096)
    )
    ps.add_argument(
        '-n', '--niter', type=int,
        help='Number of CLEAN iterations',
        metavar='NITER', default=10000
    )
    ps.add_argument(
        '-m', '--minimum_clean', type=float,
        help='Minimum clean component flux (Jy) (for iteration and stopping)',
        metavar='MIN_CLEAN', default=0.001
    )
    ps.add_argument(
        '-o', '--output_image', type=str,
        help='Output fitted continuum image file name',
        metavar='FILE', default='continuum_image.fits'
    )
    args = ps.parse_args()
    args.weak_continuum[2] = int(args.weak_continuum[2])
    args.weak_continuum[3] = int(args.weak_continuum[3])
    
    # prepare AIPS
    AIPS.userno = args.userno
    
    # load visibility data
    weak_continuum_uvdata = AIPSUVData(
        args.weak_continuum[0], args.weak_continuum[1],
        args.weak_continuum[2], args.weak_continuum[3]
    )
    
    # iteratively image the weak continuum source till satisfactory
    cellsize = float(args.imaging_params[0])
    imsize = int(args.imaging_params[1])
    rashift, decshift = 0.0, 0.0
    while True:
        print(f'Imaging with cellsize={cellsize} arcsec, imsize={imsize} pixels')
        print(f'R.A. shift={rashift} arcsec, Dec. shift={decshift} arcsec')
        beam, image = imagr(
            indata=weak_continuum_uvdata,
            cellsize=cellsize,
            imsize=imsize,
            niter=args.niter,
            params={
                'rashift|1': rashift,
                'decshift|1': decshift,
                'uvwtfn': 'NA',
                'gain': args.minimum_clean,
                'flux': -args.minimum_clean,
                'dotv': -1
            }
        )
        
        # to switch to plotly
        im_data = grab_im(image)
        x = -np.linspace(-imsize/2*cellsize, imsize/2*cellsize, imsize) + rashift
        y = np.linspace(-imsize/2*cellsize, imsize/2*cellsize, imsize) + decshift
        fig, ax = plt.subplots(figsize=(10, 8), dpi=120)
        im = ax.imshow(
            im_data, extent=(x[0], x[-1], y[0], y[-1]),
            cmap='inferno', origin='lower',
            vmin=args.minimum_clean,
        )
        plt.colorbar(im, ax=ax, label='Flux Density (Jy/beam)')
        ax.set_xlabel('R.A. Offset (arcsec)')
        ax.set_ylabel('Dec. Offset (arcsec)')
        plt.show()

        text = input('Please input "Y" to accept image, or "N" to re-image: ')
        if text.upper() == 'Y':
            break
        else:
            print('Please input new imaging parameters (cellsize, imsize, R.A. shift, Dec. shift).')
            print(f'Previous values: {cellsize}, {imsize}, {rashift}, {decshift}')
            text = input('New values (space-separated): ')
            cellsize, imsize, rashift, decshift = map(float, text.split())
            imsize = int(imsize)
            for img in (beam, image):
                img.zap()
    
    # export continuum image
    fittp(
        indata=image,
        dataout=args.output_image,
    )