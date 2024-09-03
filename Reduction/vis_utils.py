import os
import sys
from argparse import ArgumentParser

from AIPS import AIPS
from Wizardry.AIPSData import AIPSUVData
import numpy as np
from astropy.table import Table
from astropy import units as u

def grab_table(uv, table_name, table_index=0, ignore=[]):
    '''
    Grab table (AN, CL, FQ, NX, SU) from AIPSUVData object
    * need to check for BP, FG, GC, SN, TY 
    '''
    table = uv.table(table_name, table_index)
    table = Table(
        [
            [getattr(row, col).strip()
             if isinstance(getattr(row, col), str)
             else getattr(row, col)
             for row in table]
            for col in table._keys
            if col not in ignore
        ],
        names=[col for col in table._keys if col not in ignore]
        # need to add units method
    )
    return table

def grab_visibility(name, klass, seq, disk, source, mode='cross', antennas=[], baselines=[], IF=1, stokes='LL', all=True):
    '''
    Grab visibility data from AIPSUVData object
    '''
    # load UV data object
    uv = AIPSUVData(name, klass, disk, seq)
    
    # get source and antenna tables
    sources = grab_table(uv, 'SU')
    
    # initialise visibility and flag arrays
    nchan = uv.header['naxis'][uv.header['ctype'].index('FREQ')]
    if mode == 'auto': # if auto-correlations
        if not antennas: # if no antenna specified, consider all auto-correlations
            ntime = sum(
                row.baseline[0] == row.baseline[1] and 
                row.source == sources[sources['source'] == source]['id__no'][0] 
                for row in uv)
        else: # if antenna specified, consider auto-correlations for those antennas
            ntime = sum(row.baseline[0] == row.baseline[1] and 
                        (row.baseline[0] in antennas or row.baseline[1] in antennas) and 
                        row.source == sources[sources['source'] == source]['id__no'][0] 
                        for row in uv)
    elif mode == 'cross':
        if not antennas: # if no antenna specified
            if not baselines: # if no baseline specified, consider all cross-correlations
                ntime = sum(row.baseline[0] != row.baseline[1] and 
                            row.source == sources[sources['source'] == source]['id__no'][0] 
                            for row in uv)
            else: # if baseline specified, consider cross-correlations only for those baselines
                ntime = sum(row.baseline[0] != row.baseline[1] and 
                            (
                                (row.baseline[0] in baselines and row.baseline[1] in baselines) or
                                (row.baseline[1] in baselines and row.baseline[0] in baselines)
                            ) and 
                            row.source == sources[sources['source'] == source]['id__no'][0] 
                            for row in uv)
        else: # if antenna specified, consider cross-correlations only for baselines those antennas
            ntime = sum(row.baseline[0] != row.baseline[1] and 
                        (row.baseline[0] in antennas or row.baseline[1] in antennas) and 
                        row.source == sources[sources['source'] == source]['id__no'][0] 
                        for row in uv)

    visibility = Table(
        [
            np.zeros(ntime),
            np.zeros(ntime),
            np.zeros(ntime),
            np.zeros(ntime),
            np.zeros(ntime),
            np.zeros((ntime, 2)),
            np.zeros((ntime, nchan)),
            np.zeros((ntime, nchan)),
            np.zeros((ntime, nchan))
        ],
        names = ['u', 'v', 'w', 'time', 'inttime', 'baseline', 'real', 'imag', 'weig'],
        units = [u.m, u.m, u.m, u.day, u.s, None, u.Jy, u.Jy, None]
    )
    uv = AIPSUVData(name, klass, seq, disk) # reset uv object's iterator

    # grab visibilities
    i = 0
    if mode == 'auto': # if auto-correlations
        if not antennas: # if no antenna specified, consider all auto-correlations
            for row in uv:
                if (
                    row.baseline[0] == row.baseline[1] and
                    row.source == sources[sources['source'] == source]['id__no'][0]
                ):
                    visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                    visibility['time'][i] = row.time
                    visibility['inttime'][i] = row.inttim
                    visibility['baseline'][i] = row.baseline
                    visibility['real'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 0]
                    visibility['imag'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 1]
                    visibility['weig'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 2]
                    i += 1
        else: # if antenna specified, consider auto-correlations for those antennas
            for row in uv:
                if (
                    row.baseline[0] == row.baseline[1] and
                    (row.baseline[0] in antennas or row.baseline[1] in antennas) and
                    row.source == sources[sources['source'] == source]['id__no'][0] 
                ):
                    visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                    visibility['time'][i] = row.time
                    visibility['inttime'][i] = row.inttim
                    visibility['baseline'][i] = row.baseline
                    visibility['real'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 0]
                    visibility['imag'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 1]
                    visibility['weig'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 2]
                    i += 1
    elif mode == 'cross':
        if not antennas: # if no antenna specified
            if not baselines: # if no baseline specified, consider all cross-correlations
                for row in uv:
                    if (
                        row.baseline[0] != row.baseline[1] and
                        row.source == sources[sources['source'] == source]['id__no'][0]
                    ):
                        visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                        visibility['time'][i] = row.time
                        visibility['inttime'][i] = row.inttim
                        visibility['baseline'][i] = row.baseline
                        visibility['real'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 0]
                        visibility['imag'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 1]
                        visibility['weig'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 2]
                        i += 1
            else: # if baseline specified, consider cross-correlations only for those baselines
                for row in uv:
                    if (
                        row.baseline[0] != row.baseline[1] and 
                        (
                            (row.baseline[0] in baselines and row.baseline[1] in baselines) or
                            (row.baseline[1] in baselines and row.baseline[0] in baselines)
                        ) and 
                        row.source == sources[sources['source'] == source]['id__no'][0]
                    ):
                        visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                        visibility['time'][i] = row.time
                        visibility['inttime'][i] = row.inttim
                        visibility['baseline'][i] = row.baseline
                        visibility['real'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 0]
                        visibility['imag'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 1]
                        visibility['weig'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 2]
                        i += 1
        else: # if antenna specified, consider cross-correlations only for baselines with those antennas
            for row in uv:
                if (
                    (row.baseline[0] in antennas or row.baseline[1] in antennas) and
                    row.source == sources[sources['source'] == source]['id__no'][0]
                ):
                    visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                    visibility['time'][i] = row.time
                    visibility['inttime'][i] = row.inttim
                    visibility['baseline'][i] = row.baseline
                    visibility['real'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 0]
                    visibility['imag'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 1]
                    visibility['weig'][i, :] = row.visibility[IF - 1, :, uv.stokes.index(stokes) - 1, 2]
                    i += 1
    
    return visibility

def visibility_amplitude(real, imag):
    '''
    Calculates visibility amplitude
    '''
    return np.sqrt(real**2 + imag**2)

def visibility_phase(real, imag):
    '''
    Calculates visibility phase
    '''
    return np.arctan2(imag, real)

def scalar_average(real, imag, weig, axis):
    '''
    Calculates scalar average for complex visibilities
    '''
    amplitude = np.average(visibility_amplitude(real, imag), weights=weig, axis=axis)
    phase = visibility_phase(np.sum(weig*real, axis=axis), np.sum(weig*imag, axis=axis))
    return amplitude, phase

def vector_average(real, imag, weig, axis):
    '''
    Calculates vector average for complex visibilities
    '''
    avg_real, avg_imag = np.average(real, weights=weig, axis=axis), np.average(imag, weights=weig, axis=axis)
    amplitude = visibility_amplitude(avg_real, avg_imag)
    phase = visibility_phase(np.sum(weig*real, axis=axis), np.sum(weig*imag, axis=axis))
    return amplitude, phase

# ---------- #

if __name__ == "__main__":
    import matplotlib
    matplotlib.use('TkAgg')
    import matplotlib.pyplot as plt
    
    ps = ArgumentParser(description='Inspect visibility data in AIPS UV data. Produces uv-coverage, auto-correlation spectra, cross-correlation spectra, and visibility-time plots.')
    ps.add_argument('user', type=int, help='AIPS user number')
    ps.add_argument('-c', '--catalogue', type=str, nargs=4, help='Visibility catalogue information', metavar=('NAME', 'CLASS', 'SEQ', 'DISK'), required=True)
    ps.add_argument('-t', '--target', type=str, help='source to inspect')
    ps.add_argument('-i', '--IF', type=str, default=1, help='IF to inspect')
    ps.add_argument('-s', '--stokes', type=str, default='LL', help='Stokes parameter to inspect')
    ps.add_argument('-o', '--outname', type=str, default='output', help='plot output file name prefix')
    args = ps.parse_args()
    
    AIPS.userno = args.user
    
    # grab UV data object
    args.catalogue[2] = int(args.catalogue[2])
    args.catalogue[3] = int(args.catalogue[3])
    uv = AIPSUVData(
        args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2]
    )
    
    # grab antenna tables
    AN = grab_table(uv, 'AN')
    SU = grab_table(uv, 'SU')
    
    # grab visibility data
    antennas = np.repeat(AN['nosta'], 2).reshape(-1, 2)
    baselines = AN['nosta'][np.stack(np.triu_indices(len(AN), 1), axis=-1)]
    autocorr = grab_visibility(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2], args.target, mode='auto', IF=args.IF, stokes=args.stokes)
    visibility = grab_visibility(args.catalogue[0], args.catalogue[1], args.catalogue[3], args.catalogue[2], args.target, mode='cross', IF=args.IF, stokes=args.stokes)
    visibility.write('output.fits')
    
    # plot uv-coverage    
    # fig, axs = plt.subplots(figsize=(8, 8), dpi=150)
    # cmap = matplotlib.colormaps['jet'](np.linspace(0, 1, len(baselines)))
    # for baseline, colour in zip(baselines, cmap):
    #     mask = np.sum(visibility['baseline'] == baseline, axis=1).astype(bool)
    #     axs.plot(visibility['u'][mask], visibility['v'][mask], '.', ms=2, color=colour, 
    #              label=f'{AN[AN["nosta"] == baseline[0]]["anname"][0]} - {AN[AN["nosta"] == baseline[1]]["anname"][0]}')
    #     axs.plot(-visibility['u'][mask], -visibility['v'][mask], '.', ms=2, color=colour)
    # axs.legend(fontsize=4, loc='center', ncols=np.floor(np.sqrt(len(baselines))))
    # axs.set_xlabel('u (m)')
    # axs.set_ylabel('v (m)')
    # plt.savefig(f'{args.outname}_uv-coverage.png')
    # plt.close()
    
    # plot auto-correlation spectra
    # fig, axs = plt.subplots(len(AN), figsize=(8, 8), dpi=150, sharex=True,
    #                         gridspec_kw={'hspace': 0})
    # cmap = matplotlib.colormaps['jet'](np.linspace(0, 1, len(antennas)))
    # for i, (antenna, colour) in enumerate(zip(antennas, cmap)):
    #     mask = np.any(autocorr['baseline'] == antenna, axis=1).astype(bool)
    #     spectra = scalar_average(autocorr[mask]['real'], autocorr[mask]['imag'], autocorr[mask]['weig'], axis=0)
    #     axs[i].plot(spectra[0], '-', color=colour, label=f'{AN[AN["nosta"] == antenna[0]]["anname"][0]}')
    #     axs[i].legend(fontsize=8, loc='center')
    # axs[i].set_xlabel('Channels')
    # fig.supylabel('Amplitude (Jy)')
    # plt.show()