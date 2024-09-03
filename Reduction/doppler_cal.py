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

def set_velocity(uvdata, restfreq, sources, sysvel, chan, params=None):
    # set velocity parameters
    task = AIPSTask('SETJY')
    task.indata = uvdata
    task.sources = AIPSList(sources)
    task.sysvel = sysvel
    task.restfreq[1], task.restfreq[2] = restfreq
    task.veltyp = 'LSR'
    task.veldef = 'RADIO'
    task.aparm[1] = chan
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
    return AIPSUVData(output.name, output.klass, uvdata.disk, output.seq)

# -------------------- #

if __name__ == '__main__':
    ps = ArgumentParser(description='Performs Doppler velocity calibrations on spectral data.')
    ps.add_argument('userno', type=int, help='AIPS user number', metavar='USER_NO')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-r', '--restfreq', type=float, nargs=2, help='Rest frequency of spectral line (FREQ_1 + FREQ_2)', metavar=('FREQ_1', 'FREQ_2'), required=True)
    ps.add_argument('-t', '--target', type=str, nargs='+', help='Target sources to perform Doppler velocity corrections onto', metavar=('SOURCE_1', 'SOURCE_2'), required=True)
    ps.add_argument('-s', '--sysvel', type=float, help='Systemic velocity of source in km/s', metavar='VELOCITY', required=True)
    ps.add_argument('--init', type=int, help='Initial channel', metavar='CHAN', required=True)
    args = ps.parse_args()
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    
    AIPS.userno = args.userno
    
    uvdata = AIPSUVData(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2])
    
    tabed_key(uvdata, inext='AN', invers=1, key='ARRNAM', value='VLBA')
    sysvel, init = args.sysvel, args.init
    while True:
        set_velocity(uvdata, args.restfreq, args.target, sysvel, init)
        uvdata_cvel = cvel_doppler(uvdata, args.target)
        new_chan = input('Enter new channel number (or "q" to quit): ')
        if new_chan == 'q':
            break
        init = int(new_chan)
        uvdata_cvel.zap()
    tabed_key(uvdata, inext='AN', invers=1, key='ARRNAM', value='KVN')
    tabed_key(uvdata_cvel, inext='AN', invers=1, key='ARRNAM', value='KVN')
