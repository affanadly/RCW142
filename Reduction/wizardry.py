from astropy.io import fits
from astropy.table import QTable, Table
from astropy import units as u
from astropy.wcs import WCS
import numpy as np

from AIPS import AIPS
from AIPSData import AIPSImage, AIPSUVData
from Wizardry.AIPSData import AIPSImage as wAIPSImage
from Wizardry.AIPSData import AIPSUVData as wAIPSUVData

# general wizardry functions
def grab_table(data, table_name, table_index=0, ignore=[]):
    """
    Grabs a table from an AIPSUVData or AIPSImage object.
    Parameters:
        data (AIPSUVData or AIPSImage): The AIPS data object.
        table_name (str): The name of the table to retrieve.
        table_index (int, optional): The index of the table to retrieve.
        ignore (list, optional): List of columns to ignore.
    Returns:
        astropy.table.Table: The specified table as an Astropy Table.
    Notes: 
        For AIPSUVData, currently only works for AN, CL, FQ, NX, and SU 
        tables. Not tested for BP, FG, GC, SN, and TY tables. For 
        AIPSImage, currently works for CC and CG tables.
    """
    temp_data = grab_data_copy(data)

    table = temp_data.table(table_name, table_index)
    table = Table(
        data=[
            [
                getattr(row, col).strip()
                if isinstance(getattr(row, col), str)
                else getattr(row, col)
                for row in table
            ]
            for col in table._keys if col not in ignore
        ],
        names=[col for col in table._keys if col not in ignore]
    )
    return table

def grab_header(data):
    """
    Grabs the header from an AIPSUVData or AIPSImage object.
    Parameters:
        data (AIPSUVData or AIPSImage): The AIPS data object.
    Returns:
        astropy.io.fits.Header: The header of the AIPS data object.
    """
    temp_data = grab_data_copy(data)
    header_dict = temp_data.header._generate_dict()
    for i, _ in enumerate(header_dict['naxis']):
        if header_dict['crval'][i] != 0 \
        and header_dict['crpix'][i] != 0 \
        and header_dict['cdelt'][i] != 0:
            for key in ['naxis', 'ctype', 'crval', 'cdelt', 'crpix', 'crota']:
                header_dict[f'{key.upper()}{i + 1}'] = header_dict[key][i]
    for key in ['naxis', 'ctype', 'crval', 'cdelt', 'crpix', 'crota', 'ptype']:
        if key in header_dict:
            del header_dict[key]
    # return header_dict
    return fits.Header(header_dict)

def grab_wcs(data):
    """
    Grabs the WCS from an AIPSUVData or AIPSImage object.
    Parameters:
        data (AIPSUVData or AIPSImage): The AIPS data object.
    Returns:
        astropy.wcs.WCS: The WCS of the AIPS data object.
    """
    header = grab_header(data)
    return WCS(header)

# data wizardry functions
def grab_uv(
    uvdata, source, corr='cross', 
    antennas=[], baselines=[], IF=1, stokes='LL'
):
    """
    Grabs the UV data for a specific source from an AIPSUVData object.
    Parameters:
        uvdata (AIPSUVData): The AIPS UV data object.
        source (str): The source name to filter by.
        corr (str, optional): The correlation of data to grab ('cross', 
            'auto', 'both').
        antennas (list, optional): List of antennas to filter by.
        baselines (list, optional): List of baselines to filter by.
        IF (int, optional): The IF number to filter by.
        stokes (str, optional): The Stokes parameter to filter by.
    Returns:
        astropy.table.QTable: The filtered UV data as an Astropy QTable.
    Notes:
        Currently only works for AIPSUVData objects with spectral FREQ
        channels, and not VELO- or FELO- spectral channels.
    """
    def get_source_id(sources, source_name):
        # get source ID from the source list
        return sources[sources['source'] == source_name]['source_id'][0]
    
    def match_row(row, source_id, corr):
        # match row based on source, correlation, antennas, and baselines
        source_match = row.source == source_id
        baseline1, baseline2 = row.baseline
        is_auto = baseline1 == baseline2
        is_cross = baseline1 != baseline2
        has_antenna = (baseline1 in antennas or baseline2 in antennas)
        has_baseline = (
            (baseline1 in baselines and baseline2 in baselines) or
            (baseline2 in baselines and baseline1 in baselines)
        )
        
        if corr == 'auto':
            return source_match and is_auto and (not antennas or has_antenna)
        elif corr == 'cross':
            if antennas:
                return source_match and is_cross and has_antenna
            elif baselines:
                return source_match and is_cross and has_baseline
            else:
                return source_match and is_cross
        return False
    
    def fill_row(visibility, i, row, stokes_id):
        # fill the visibility table row with data
        visibility['u'][i], visibility['v'][i], visibility['w'][i] = row.uvw
        visibility['time'][i] = row.time
        visibility['inttime'][i] = row.inttim
        visibility['baseline'][i] = row.baseline
        visibility['real'][i, :] = row.visibility[IF - 1, :, stokes_id, 0]
        visibility['imag'][i, :] = row.visibility[IF - 1, :, stokes_id, 1]
        visibility['weig'][i, :] = row.visibility[IF - 1, :, stokes_id, 2]

    # load UV data and get parameters
    temp_uv = wAIPSUVData(uvdata.name, uvdata.klass, uvdata.disk, uvdata.seq)
    sources = grab_table(temp_uv, 'SU')
    source_id = get_source_id(sources, source)
    stokes_id = temp_uv.stokes.index(stokes) - 1
    nchan = temp_uv.header['naxis'][temp_uv.header['ctype'].index('FREQ')]
    ntime = np.count_nonzero(
        [match_row(row, source_id, corr) for row in temp_uv]
    )
    
    # initialize visibility table
    visibility = Table(
        data=[
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
        names=[
            'u', 'v', 'w', 
            'time', 'inttime', 'baseline', 
            'real', 'imag', 'weig'
        ],
        units=[u.m, u.m, u.m, u.day, u.s, None, u.Jy, u.Jy, None]
    )
    
    # populate visibility table
    temp_uv = wAIPSUVData(
        temp_uv.name, temp_uv.klass, temp_uv.disk, temp_uv.seq
    )
    i = 0
    for row in temp_uv:
        if match_row(row, source_id, corr):
            fill_row(visibility, i, row, stokes_id)
            i += 1
    return visibility

def grab_im(imdata):
    """
    Grabs the image data from an AIPSImage object.
    Parameters:
        imdata (AIPSImage): The AIPS image data object.
    Returns:
        ndarray: The pixel data of the image.
    Notes:
        Currently only works for AIPSImage objects with 2D data.
    """
    temp_im = wAIPSImage(imdata.name, imdata.klass, imdata.disk, imdata.seq)
    temp_im.squeeze()
    return temp_im.pixels

    # try:
    #     return temp_im.pixels()
    # except ValueError:
    #     x, y, z = tuple(temp_im.header['naxis'][:3])
    #     image = []
    #     for i in range(z):
    #         temp_im._data.ReadPlane(
    #             temp_im._err, 
    #             blc=[1, 1, i + 1], 
    #             trc=[x + 1, y + 1, i + 1]
    #         )
    #         image.append(np.frombuffer(temp_im._data.PixBuf))
    #     return np.array(image)

# calculation functions
def uv_amplitude(real, imag):
    """
    Calculate the visibility amplitude from real and imaginary 
    components.
    Parameters:
        real (array-like): Real part of the visibilities.
        imag (array-like): Imaginary part of the visibilities.
    Returns:
        ndarray: Amplitude of the visibilities.
    """
    return np.sqrt(real**2 + imag**2)

def uv_phase(real, imag):
    """
    Calculate the visibility phase from real and imaginary 
    components.
    Parameters:
        real (array-like): Real part of the visibilities.
        imag (array-like): Imaginary part of the visibilities.
    Returns:
        ndarray: Phase of the visibilities in radians.
    """
    return np.arctan2(imag, real)

def scalar_average(real, imag, weig, axis):
    """
    Calculate the scalar average amplitude and phase for complex 
    visibilities.
    Parameters:
        real (array-like): Real part of the visibilities.
        imag (array-like): Imaginary part of the visibilities.
        weig (array-like): Weights for averaging.
        axis (int): Axis along which to average.
    Returns:
        tuple: (amplitude, phase) where amplitude is the weighted 
            average of the amplitudes, and phase is the phase of the 
            weighted sum.
    """
    amplitude = np.average(uv_amplitude(real, imag), weights=weig, axis=axis)
    phase = uv_phase(
        np.sum(weig*real, axis=axis), 
        np.sum(weig*imag, axis=axis)
    )
    return amplitude, phase

def vector_average(real, imag, weig, axis):
    """
    Calculate the vector average amplitude and phase for complex 
    visibilities.
    Parameters:
        real (array-like): Real part of the visibilities.
        imag (array-like): Imaginary part of the visibilities.
        weig (array-like): Weights for averaging.
        axis (int): Axis along which to average.

    Returns:
        tuple: (amplitude, phase) where amplitude is the amplitude of 
            the weighted average vector, and phase is the phase of the 
            weighted sum.
    """
    avg_real = np.average(real, weights=weig, axis=axis)
    avg_imag = np.average(imag, weights=weig, axis=axis)
    amplitude = uv_amplitude(avg_real, avg_imag)
    phase = uv_phase(
        np.sum(weig*real, axis=axis), 
        np.sum(weig*imag, axis=axis)
    )
    return amplitude, phase

# utility functions
def grab_data_copy(data):
    # Grabs a copy of the AIPS data object.
    if isinstance(data, AIPSUVData) or isinstance(data, wAIPSUVData):
        return wAIPSUVData(data.name, data.klass, data.disk, data.seq)      
    elif isinstance(data, AIPSImage) or isinstance(data, wAIPSImage):
        return wAIPSImage(data.name, data.klass, data.disk, data.seq)
    else:
        raise TypeError("data must be an AIPSUVData or AIPSImage object.")

def switch_spectral(data):
    '''
    Converts the frequency axis of an AIPSUVData or AIPSImage to 
    velocity (and vice versa), based on OTObit.altswitch
    '''
    temp_data = grab_data_copy(data)
    hd = temp_data._data.Desc.Dict 
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
        if hd["VelReference"] == 1:
            hd["ctype"][i] = ctype + "-LSR"
        elif hd["VelReference"] ==  2:
            hd["ctype"][i] = ctype + "-HEL"
        elif hd["VelReference"] == 3:
            hd["ctype"][i] = ctype + "-OBS"
        else:
            hd["ctype"][i] = ctype + "-LSR"
            hd["VelReference"] = 1
        tCrpix = hd["crpix"][i]
        tCrval = hd["crval"][i]
        hd["crpix"][i] = hd["altCrpix"]
        hd["crval"][i] = hd["altRef"]
        delnu   = hd["cdelt"][i]
        refnu   = tCrval
        frline  = hd["altCrpix"]
        dvzero  = hd["altRef"]
        hd["cdelt"][i] = - delnu * (velite + vsign * dvzero) / \
                         (refnu + delnu * (frline - tCrpix))
        hd["altCrpix"] = tCrpix
        hd["altRef"]   = tCrval
    if (frqType[0:4] == "VELO") or (frqType[0:4] == "FELO"):
        if frqType[0:4] == "FELO":
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

    temp_data._data.Desc.Dict = hd
    temp_data.update()
    return
