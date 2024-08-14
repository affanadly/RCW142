from argparse import ArgumentParser

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

from tasks import *

def tabed_key(uvdata, inext, invers, key, value, params=None):
    # edit table entry
    task = AIPSTask('TABED')
    task.indata = uvdata
    task.inext = inext
    task.invers = invers
    task.optype = 'KEY'
    task.aparm[4] = 3
    task.keyword = key
    task.keystrng = value
    parse_params(task, params)
    task.go()

def set_velocity(uvdata, restfreq, sources, params=None):
    # set velocity parameters
    task = AIPSTask('SETJY')
    task.indata = uvdata
    task.sources = AIPSList(sources)
    task.optype = 'VCAL'
    task.restfreq[1], task.restfreq[2] = restfreq
    task.veltyp = 'LSR'
    task.veldef = 'RADIO'
    parse_params(task, params)
    task.go()

def cvel_doppler(uvdata, sources, freqid=1, params=None):
    initial = grab_catalogue(uvdata.disk)
    
    # apply Doppler correction
    task = AIPSTask('CVEL')
    task.indata = uvdata
    task.sources = AIPSList(sources)
    task.freqid = freqid
    task.aparm[4] = 1
    task.aparm[10] = 1
    parse_params(task, params)
    task.go()
    
    final = grab_catalogue(uvdata.disk)
    output = compare_catalogues(initial, final)
    return AIPSUVData(output.name, output.klass, output.disk, output.seq)

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Sets velocity parameters and performs Doppler velocity calculations.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-m', '--master', type=str, nargs=4, help='Master catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-r', '--restfreq', type=float, nargs=2, help='Rest frequency of spectral line (FREQ_1 + FREQ_2)', metavar=('FREQ_1', 'FREQ_2'), required=True)
    ps.add_argument('-s', '--sources', type=str, nargs='+', help='Sources to perform Doppler velocity corrections onto', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    args = ps.parse_args()
    
    AIPS.userno = args.userno
    
    master = AIPSUVData(args.master[0], args.master[1], int(args.master[3]), int(args.master[2]))
    
    tabed_key(master, inext='AN', invers=1, key='ARRNAM', value='VLBA')
    set_velocity(master, args.restfreq, args.sources)
    master_cvel = cvel_doppler(master, args.sources)
    tacop(master, master_cvel, inext='BP', invers=1, ncount=1)
    tabed_key(master, inext='AN', invers=1, key='ARRNAM', value='KAVA')
