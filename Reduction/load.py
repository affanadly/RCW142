from argparse import ArgumentParser

from AIPS import AIPS

from KaVA_pipeline import fitld, msort, indxr

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Loads, sorts, and indexes visibility data from a FITS file into AIPS.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-f', '--file', type=str, help='Visibility file name to load', metavar='FILE', required=True)
    ps.add_argument('-s', '--sources', type=str, nargs='+', help='Sources to read in file', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('-d', '--disk', type=int, help='AIPS disk number to load into', required=True)
    ps.add_argument('-i', '--clint', type=float, help='Integration time in minutes', required=True)
    args = ps.parse_args()
    
    AIPS.userno = args.userno
    
    # load file, sort, and index
    uvdata = fitld(args.file, args.disk, args.clint, args.sources, 
                   params={
                       'douvcomp': 1,
                       'doconcat': -1,
                       'digicor': -1,
                       'wtthresh': 0.8
                   }
                )
    sorted_uvdata = msort(uvdata, params={'sort': 'TB'})
    uvdata.zap()
    indxr(sorted_uvdata, args.clint)