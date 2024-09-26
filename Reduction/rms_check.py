from argparse import ArgumentParser

from AIPS import AIPS
from AIPSData import AIPSUVData

import numpy as np

from tasks import imagr
from wiz import grab_im

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Calculates RMS for KaVA Star Formation LP data.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('--channel', type=int, help='Line free channel', metavar='CHAN', required=True)
    ps.add_argument('--cellsize', type=float, help='Cell size in arcseconds', default=1e-3)
    ps.add_argument('--imsize', type=int, help='Image size in pixels', default=8192)
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # prepare AIPS
    AIPS.userno = args.userno
    
    # load visibility data
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    
    # perform imaging
    images = imagr(uvdata, args.cellsize, args.imsize, params={
        'bchan': args.channel,
        'echan': args.channel,
    })
    rms = np.std(grab_im(images[1]).flatten())
    for image in images:
        image.zap()
    print(f'RMS: {rms} Jy/beam')