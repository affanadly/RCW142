from argparse import ArgumentParser

from AIPS import AIPS
from AIPSData import AIPSUVData

from tasks import fittp

# ----- #

if __name__ == '__main__':
    """
    This script grabs visibility data from an AIPS UV data set and
    writes it to a FITS file.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='Grab Visibilities',
        description='''Grabs visibility data from an AIPS UV data set and
            writes it to a FITS file.''',
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
        '-o', '--output', type=str,
        help='Output FITS file name',
        metavar='OUTPUT', default='visibilities.fits'
    )
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    # prepare AIPS
    AIPS.userno = args.userno
    
    # load visibility data
    uvdata = AIPSUVData(
        args.catalogue[0], args.catalogue[1],
        args.catalogue[2], args.catalogue[3]
    )
    
    # export to FITS
    fittp(indata=uvdata, dataout=args.output)
