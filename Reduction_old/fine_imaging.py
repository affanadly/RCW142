from argparse import ArgumentParser

from AIPS import AIPS
from AIPSData import AIPSUVData

from astropy.table import Table
from astropy import units as u

from tasks import imagr
from wiz import switch_spectral

if __name__ == '__main__':
    ps = ArgumentParser(description='Fine imaging for KaVA Star Formation LP data.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('--fields', type=str, help='Fields text file', metavar='FIELDS', required=True)
    ps.add_argument('--shift', type=float, nargs=2, help='Shift in arcseconds', metavar=('RASHIFT', 'DECSHIFT'), default=[0, 0])
    ps.add_argument('--niter', type=int, help='Number of iterations', default=500)
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # prepare AIPS
    AIPS.userno = args.userno
    
    # load visibility data and fields
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    fields = Table.read(args.fields, format='ascii')
    
    # perform imaging
    images = []
    for field in fields:
        _, image = imagr(uvdata, float(field['cellsize']), int(field['imsize']), niter=args.niter, params={
            'bchan': int(field['bchan']),
            'echan': int(field['echan']),
            'rashift|1': float(field['rashift']),
            'decshift|1': float(field['decshift']),
        })
        switch_spectral(image)
        images.append(image)