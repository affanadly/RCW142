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
    ps.add_argument('-m', '--master', type=str, nargs=4, help='Master catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-a', '--auxiliary', type=str, nargs=4, help='Auxiliary catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-f', '--flagfile', type=str, help='YAML flag file name to apply', metavar='FLAG_FILE', required=True)
    args = ps.parse_args()
    args.master[2] = int(args.master[2])
    args.master[3] = int(args.master[3])
    args.auxiliary[2] = int(args.auxiliary[2])
    args.auxiliary[3] = int(args.auxiliary[3])
    
    AIPS.userno = args.userno
    
    # load flag file
    with open(args.flagfile, 'r') as file:
        flags = list(yaml.safe_load_all(file))
    
    # load catalogues
    master = AIPSUVData(args.master[0], args.master[1], args.master[3], args.master[2])
    auxiliary = AIPSUVData(args.auxiliary[0], args.auxiliary[1], args.auxiliary[3], args.auxiliary[2])
    
    # flag visibilities
    for flag in flags:
        if (
            flag['name'] == master.name and
            flag['klass'] == master.klass and
            flag['disk'] == master.disk and
            flag['seq'] == master.seq
        ):
            uvflg(master, outfgver=1, params={
                key: AIPSList(value)
                if type(value) == list
                else value
                for key, value in flag.items()
                if key not in ['name', 'klass', 'disk', 'seq']
            })
        elif (
            flag['name'] == auxiliary.name and
            flag['klass'] == auxiliary.klass and
            flag['disk'] == auxiliary.disk and
            flag['seq'] == auxiliary.seq
        ):
            uvflg(auxiliary, outfgver=1, params={
                key: AIPSList(value)
                if type(value) == list
                else value
                for key, value in flag.items()
                if key not in ['name', 'klass', 'disk', 'seq']
            })