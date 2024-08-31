from argparse import ArgumentParser
import yaml

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from utils import *
from tasks import *

def uvflg(uvdata, outfgver, params=None):
    # flags visibilities based on params
    task = AIPSTask('UVFLG')
    task.indata = uvdata
    task.outfgver = outfgver
    parse_params(task, params)
    task.go()

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Flags visibilities based on user-defined parameters.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-f', '--flagfile', type=str, help='YAML flag file name to apply', metavar='FLAG_FILE', required=True)
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])

    AIPS.userno = args.userno
    
    # load flag file
    with open(args.flagfile, 'r') as file:
        flags = list(yaml.safe_load_all(file))
    
    # load catalogue
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    
    # flag visibilities
    for flag in flags:
        uvflg(uvdata, outfgver=1, params={
            key: AIPSList(value)
            if type(value) == list
            else value
            for key, value in flag.items()
        })