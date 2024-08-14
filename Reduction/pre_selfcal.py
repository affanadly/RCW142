from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from tasks import *

def split_peak(uvdata, target, channel, params=None):
    initial = grab_catalogue(uvdata.disk)
    
    # split peak channel
    task = AIPSTask('SPLIT')
    task.indata = uvdata
    task.sources = AIPSList(target)
    task.bchan = channel
    task.echan = channel
    task.aparm[1] = 1
    parse_params(task, params)
    task.go()
    
    final = grab_catalogue(uvdata.disk)
    output = compare_catalogues(initial, final)
    return AIPSUVData(output.name, output.klass, output.disk, output.seq)

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Creates a single channel catalogue of the peak channel of a target source and writes it to a FITS file for self-calibration.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-m', '--master', type=str, nargs=4, help='Master catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-t', '--target', type=str, help='Target maser source for self-calibration', metavar='SOURCE', required=True)
    ps.add_argument('-c', '--chan', type=int, help='Channel for self-calibration', metavar='CHANNEL', required=True)
    ps.add_argument('-o', '--output', type=str, help='Output FITS file name', metavar='OUTPUT_FILE', default='output.fits')
    args = ps.parse_args()
    args.master[2] = int(args.master[2])
    args.master[3] = int(args.master[3])
    
    AIPS.userno = args.userno
    
    master = AIPSUVData(args.master[0], args.master[1], args.master[3], args.master[2])
    
    master_peak = split_peak(master, args.target, args.peak_chan, params={
        'docalib': 1,
        'gainuse': 7,
        'doband': 1,
        'bpver': 1,
        'outname': args.target,
        'outclass': 'PCHAN'
    })
    fittp(master_peak, args.output)
