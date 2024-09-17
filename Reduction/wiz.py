from AIPS import AIPS
from Wizardry.AIPSData import AIPSUVData, AIPSImage

import numpy as np
from astropy.io import fits
from astropy.table import Table
from astropy import units as u
from astropy.wcs import WCS

def grab_uv_table(uv, table_name, table_index=0, ignore=[]):
    '''
    Grab table (AN, CL, FQ, NX, SU) from AIPSUVData object
    * need to check for BP, FG, GC, SN, TY 
    '''
    temp_uv = AIPSUVData(uv.name, uv.klass, uv.disk, uv.seq)
    
    table = temp_uv.table(table_name, table_index)
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
    )
    return table

def grab_uv(uv, source, mode='cross', antennas=[], baselines=[], IF=1, stokes='LL'):
    '''
    Grab visibility data from AIPSUVData object
    '''
    # load UV data object
    temp_uv = AIPSUVData(uv.name, uv.klass, uv.disk, uv.seq)
    
    # get source and antenna tables
    sources = grab_uv_table(temp_uv, 'SU')
    
    # initialise visibility and flag arrays
    nchan = temp_uv.header['naxis'][temp_uv.header['ctype'].index('FREQ')]
    if mode == 'auto': # if auto-correlations
        if not antennas: # if no antenna specified, consider all auto-correlations
            ntime = sum(
                row.baseline[0] == row.baseline[1] and 
                row.source == sources[sources['source'] == source]['id__no'][0] 
                for row in temp_uv)
        else: # if antenna specified, consider auto-correlations for those antennas
            ntime = sum(row.baseline[0] == row.baseline[1] and 
                        (row.baseline[0] in antennas or row.baseline[1] in antennas) and 
                        row.source == sources[sources['source'] == source]['id__no'][0] 
                        for row in temp_uv)
    elif mode == 'cross':
        if not antennas: # if no antenna specified
            if not baselines: # if no baseline specified, consider all cross-correlations
                ntime = sum(row.baseline[0] != row.baseline[1] and 
                            row.source == sources[sources['source'] == source]['id__no'][0] 
                            for row in temp_uv)
            else: # if baseline specified, consider cross-correlations only for those baselines
                ntime = sum(row.baseline[0] != row.baseline[1] and 
                            (
                                (row.baseline[0] in baselines and row.baseline[1] in baselines) or
                                (row.baseline[1] in baselines and row.baseline[0] in baselines)
                            ) and 
                            row.source == sources[sources['source'] == source]['id__no'][0] 
                            for row in temp_uv)
        else: # if antenna specified, consider cross-correlations only for baselines those antennas
            ntime = sum(row.baseline[0] != row.baseline[1] and 
                        (row.baseline[0] in antennas or row.baseline[1] in antennas) and 
                        row.source == sources[sources['source'] == source]['id__no'][0] 
                        for row in temp_uv)

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
    temp_uv = AIPSUVData(temp_uv.name, temp_uv.klass, temp_uv.disk, temp_uv.seq) # reset uv object's iterator

    # grab visibilities
    i = 0
    if mode == 'auto': # if auto-correlations
        if not antennas: # if no antenna specified, consider all auto-correlations
            for row in temp_uv:
                if (
                    row.baseline[0] == row.baseline[1] and
                    row.source == sources[sources['source'] == source]['id__no'][0]
                ):
                    visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                    visibility['time'][i] = row.time
                    visibility['inttime'][i] = row.inttim
                    visibility['baseline'][i] = row.baseline
                    visibility['real'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 0]
                    visibility['imag'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 1]
                    visibility['weig'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 2]
                    i += 1
        else: # if antenna specified, consider auto-correlations for those antennas
            for row in temp_uv:
                if (
                    row.baseline[0] == row.baseline[1] and
                    (row.baseline[0] in antennas or row.baseline[1] in antennas) and
                    row.source == sources[sources['source'] == source]['id__no'][0] 
                ):
                    visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                    visibility['time'][i] = row.time
                    visibility['inttime'][i] = row.inttim
                    visibility['baseline'][i] = row.baseline
                    visibility['real'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 0]
                    visibility['imag'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 1]
                    visibility['weig'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 2]
                    i += 1
    elif mode == 'cross':
        if not antennas: # if no antenna specified
            if not baselines: # if no baseline specified, consider all cross-correlations
                for row in temp_uv:
                    if (
                        row.baseline[0] != row.baseline[1] and
                        row.source == sources[sources['source'] == source]['id__no'][0]
                    ):
                        visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                        visibility['time'][i] = row.time
                        visibility['inttime'][i] = row.inttim
                        visibility['baseline'][i] = row.baseline
                        visibility['real'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 0]
                        visibility['imag'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 1]
                        visibility['weig'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 2]
                        i += 1
            else: # if baseline specified, consider cross-correlations only for those baselines
                for row in temp_uv:
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
                        visibility['real'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 0]
                        visibility['imag'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 1]
                        visibility['weig'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 2]
                        i += 1
        else: # if antenna specified, consider cross-correlations only for baselines with those antennas
            for row in temp_uv:
                if (
                    (row.baseline[0] in antennas or row.baseline[1] in antennas) and
                    row.source == sources[sources['source'] == source]['id__no'][0]
                ):
                    visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
                    visibility['time'][i] = row.time
                    visibility['inttime'][i] = row.inttim
                    visibility['baseline'][i] = row.baseline
                    visibility['real'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 0]
                    visibility['imag'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 1]
                    visibility['weig'][i, :] = row.visibility[IF - 1, :, temp_uv.stokes.index(stokes) - 1, 2]
                    i += 1
    return visibility

def uv_amplitude(real, imag):
    '''
    Calculates visibility amplitude
    '''
    return np.sqrt(real**2 + imag**2)

def uv_phase(real, imag):
    '''
    Calculates visibility phase
    '''
    return np.arctan2(imag, real)

def scalar_average(real, imag, weig, axis):
    '''
    Calculates scalar average for complex visibilities
    '''
    amplitude = np.average(uv_amplitude(real, imag), weights=weig, axis=axis)
    phase = uv_phase(np.sum(weig*real, axis=axis), np.sum(weig*imag, axis=axis))
    return amplitude, phase

def vector_average(real, imag, weig, axis):
    '''
    Calculates vector average for complex visibilities
    '''
    avg_real, avg_imag = np.average(real, weights=weig, axis=axis), np.average(imag, weights=weig, axis=axis)
    amplitude = uv_amplitude(avg_real, avg_imag)
    phase = uv_phase(np.sum(weig*real, axis=axis), np.sum(weig*imag, axis=axis))
    return amplitude, phase

def grab_im_table(im, table_name, table_index=0, ignore=[]):
    '''
    Grab table (CC and CG) from AIPSImage object
    '''
    temp_im = AIPSImage(im.name, im.klass, im.disk, im.seq)
    
    table = temp_im.table(table_name, table_index)
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
    )
    return table

def grab_im(im):
    '''
    Grab image from AIPSImage object
    '''   
    return AIPSImage(im.name, im.klass, im.disk, im.seq).pixels

def grab_im_header(im):
    '''
    Grab image header from AIPSImage object
    ''' 
    temp_im = AIPSImage(im.name, im.klass, im.disk, im.seq)
    
    header_dict = temp_im.header._generate_dict()
    for i, _ in enumerate(header_dict['naxis']):
        if header_dict['crval'][i] == 0 and header_dict['crpix'][i] == 0 and header_dict['cdelt'][i] == 0:
            continue
        for key in ['naxis', 'ctype', 'crval', 'cdelt', 'crpix', 'crota']:
            header_dict[f'{key.upper()}{i+1}'] = header_dict[key][i]
    for key in ['naxis', 'ctype', 'crval', 'cdelt', 'crpix', 'crota']:
        del header_dict[key]
    return fits.Header(header_dict)

def grab_im_wcs(im):
    '''
    Grab WCS data from AIPSImage object
    ''' 
    return WCS(grab_im_header(im))

def switch_spectral(im):
    '''
    Converts the frequency axis of an AIPSImage to velocity (and vice versa), 
    based on OTObit.altswitch
    '''
    temp_im = AIPSImage(im.name, im.klass, im.disk, im.seq)
    
    hd = temp_im._data.Desc.Dict 
    velite = 2.997924562e8
    
    i = hd["jlocf"]
    frqType = hd["ctype"][i]
    if frqType[0:4]=="FREQ":
        if  hd["VelDef"]==1:
            vsign = -1.0
            ctype = "VELO"
        else:
            vsign = 1.0
            ctype = "FELO"
        if hd["VelReference"]==1:
            hd["ctype"][i] = ctype+"-LSR"
        elif hd["VelReference"]==2:
            hd["ctype"][i] = ctype+"-HEL"
        elif hd["VelReference"]==3:
            hd["ctype"][i] = ctype+"-OBS"
        else:
            hd["ctype"][i] = ctype+"-LSR"
            hd["VelReference"] = 1
        tCrpix = hd["crpix"][i]
        tCrval = hd["crval"][i]
        hd["crpix"][i] = hd["altCrpix"]
        hd["crval"][i] = hd["altRef"]
        delnu   = hd["cdelt"][i]
        refnu   = tCrval
        frline  = hd["altCrpix"]
        dvzero  = hd["altRef"]
        hd["cdelt"][i] = -delnu * (velite + vsign * dvzero) / \
                         (refnu + delnu * (frline - tCrpix))
        hd["altCrpix"] = tCrpix
        hd["altRef"]   = tCrval
    if (frqType[0:4]=="VELO") or (frqType[0:4]=="FELO"):
        if frqType[0:4]=="FELO":
            vsign = 1.0
        else:
            vsign = -1.0
        hd["ctype"][i] = "FREQ    "
        tCdelt = hd["cdelt"][i]
        tCrpix = hd["crpix"][i]
        tCrval = hd["crval"][i]
        delnu  = -tCdelt * hd["altRef"] / \
                (velite + vsign * tCrval + tCdelt * (tCrpix - hd["altCrpix"]))
        hd["crpix"][i] = hd["altCrpix"]
        hd["crval"][i] = hd["altRef"]
        hd["altCrpix"] = tCrpix
        hd["altRef"]   = tCrval
        hd["cdelt"][i] = delnu

    temp_im._data.Desc.Dict = hd
    temp_im.update()
    return