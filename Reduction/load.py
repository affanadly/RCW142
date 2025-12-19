from argparse import ArgumentParser

from AIPS import AIPS

from tasks import fitld, msort, indxr

# ----- #

if __name__ == '__main__':
    """
    This script loads, sorts, and indexes visibility data from a FITS 
    file into AIPS.
    """
    # parse arguments
    ps = ArgumentParser(
        prog='Load',
        description='''Loads, sorts, and indexes visibility data from a 
            FITS file into AIPS.''',
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
        '-s', '--sources', type=str, nargs='+', 
        help='Sources to read in file', 
        metavar=('SOURCE_1', 'SOURCE_2'), required=True
    )
    ps.add_argument(
        '-d', '--disk', type=int, 
        help='AIPS disk number to load into', 
        default=1
    )
    ps.add_argument(
        '-i', '--clint', type=float, 
        help='Integration time in minutes', 
        default=0.0273
    )
    args = ps.parse_args()

    # prepare AIPS
    AIPS.userno = args.userno
    
    # load file, sort, and index
    uvdata = fitld(
        datain=args.file,
        outdisk=args.disk,
        sources=args.sources,
        clint=args.clint,
        params={
            'douvcomp': 1,
            'doconcat': -1,
            'digicor': -1,
            'wtthresh': 0.8
        }
    )
    sorted_uvdata = msort(indata=uvdata, sort='TB')
    uvdata.zap()
    indxr(indata=sorted_uvdata, solint=args.clint)
