# Loading Data

Loads both the master file (containing the target, RCW142 and primary calibrator, NRAO530) and the auxiliary file (containing the primary calibrator, NRAO530 and secondary calibrator, J1752-29) into AIPS. The visibilities in the catalogues are then sorted and indexed. 

Note: The auxiliary file is loaded only for the first IF as it covers the whole frequency range of the master file. The auxiliary file only has 64 channels, unlike the master file that has 1024. 

**ParselTongue**

Syntax:

```
ParselTongue load.py [-h] USER_NO -m MASTER_FILE -a AUXILIARY_FILE -s SOURCE_1 [SOURCE_2 ...] -d DISK [-cl CLINT] 
```

| Name        | Flag | Arguments               | Description                            |
| ----------- | ---- | ----------------------- | -------------------------------------- |
| USER_NO     |      |                         | AIPS user number                       |
| --help      | -h   |                         | Displays help message                  |
| --master    | -m   | MASTER_FILE             | Master visibility file name to load    |
| --auxiliary | -a   | AUXILIARY_FILE          | Auxiliary visibility file name to load |
| --sources   | -s   | SOURCE_1, [SOURCE_2, …] | Sources to read in files               |
| --disk      | -d   | DISK                    | AIPS disk number to load into          |
| --clint     | -cl  | CLINT                   | Integration time in minutes            |

Usage in this context:

```
ParselTongue load.py <user no> -m <exper code>/<master file> -a <exper code>/<auxiliary file> -s NRAO530 J1752-29 RCW142 -d 1 -cl 0.0273
```

# Flagging

Performs flagging on both the master and auxiliary catalogues based on a YAML flag file created based on manual inspection of visibilities in both catalogues. 

**ParselTongue:**

Syntax:

```
ParselTongue flag.py USER_NO [-h] -m NAME CLASS SEQ DISK -a NAME CLASS SEQ DISK -f FLAG_FILE 
```

| Name        | Flag | Arguments           | Description                     |
| ----------- | ---- | ------------------- | ------------------------------- |
| USER_NO     |      |                     | AIPS user number                |
| --help      | -h   |                     | Displays help message           |
| --master    | -m   | NAME CLASS SEQ DISK | Master catalogue information    |
| --auxiliary | -a   | NAME CLASS SEQ DISK | Auxiliary catalogue information |
| --flagfile  | -f   | FLAG_FILE           | YAML flag file name to apply    | 

Usage in this context: 

```
ParselTongue flag.py <user no> -m MASTR MSORT 1 1 -a AUXIL MSORT 1 1 -f <exper code>/<exper code>.flag
```

# Amplitude Calibration

Correct amplitudes in cross-correlation spectra due to errors in sampler thresholds based on auto-correlation spectra, loads antenna gain and system temperature data from ANTAB files, generate amplitude calibration solutions, and generate amplitude bandpass table from primary calibrator (NRAO530).

**ParselTongue:**

Syntax: 

```
ParselTongue amp_cal.py USER_NO [-h] -m NAME CLASS SEQ DISK -a NAME CLASS SEQ DISK -f FLAGVER --accor_solint ACCOR_SOLINT --antab_file ANTAB_FILE [--apcal_solint APCAL_SOLINT] --bpass_sources SOURCE_1 [SOURCE_2 ...]
```

| Name            | Flag | Arguments               | Description                                     |
| --------------- | ---- | ----------------------- | ----------------------------------------------- |
| USER_NO         |      |                         | AIPS user number                                |
| --help          | -h   |                         | Displays help message                           |
| --master        | -m   | NAME CLASS SEQ DISK     | Master catalogue information                    |
| --auxiliary     | -a   | NAME CLASS SEQ DISK     | Auxiliary catalogue information                 |
| --flagver       | -f   | FLAGVER                 | Flag table version to apply                     | 
| --accor_solint  |      | ACCOR_SOLINT            | ACCOR solution interval in minutes              |
| --antab_file    |      | ANTAB_FILE              | ANTAB file to apply                             |
| --apcal_solint  |      | APCAL_SOLINT            | APCAL solution interval in minutes (default: 0) |
| --bpass_sources |      | SOURCE_1, [SOURCE_2, …] | Sources to use for BPASS                        |

Usage in this context:

```
ParselTongue amp_cal.py <user no> -m MASTR MSORT 1 1 -a AUXIL MSORT 1 1 -f 1 --accor_solint 0.0273 --antab_file <exper code>/ANTAB<exper code>.txt --bpass_sources NRAO530
```

# Continuum Delay Calibrations

Performs fringe fitting on primary calibrator (NRAO530) to correct for station clock synchronization residual errors, fringe fitting on secondary calibrator (J1752-29) to correct for atmospheric fluctuations, fringe fitting on primary calibrator (NRAO530) and generate phase bandpass table from primary calibrator (NRAO530).

**ParselTongue:**

Syntax: 

```
ParselTongue continuum_cal USER_NO [-h] -m NAME CLASS SEQ DISK -a NAME CLASS SEQ DISK [-f FLAGVER] --primary SOURCE_1 [SOURCE_2 ...] --secondary SOURCE_1 [SOURCE_2 ...] --refant REFANT --search ANTENNA_1 [ANTENNA_2 ...] [--clock_int SOLINT] [--clock_win DELAY RATE] [--atmos_int SOLINT] [--atmos_win DELAY RATE] [--bpass_int SOLINT]
```

| Name        | Flag | Arguments               | Description                                                             |
| ----------- | ---- | ----------------------- | ----------------------------------------------------------------------- |
| USER_NO     |      |                         | AIPS user number                                                        |
| --help      | -h   |                         | Displays help message                                                   |
| --master    | -m   | NAME CLASS SEQ DISK     | Master catalogue information                                            |
| --auxiliary | -a   | NAME CLASS SEQ DISK     | Auxiliary catalogue information                                         |
| --flagver   | -f   | FLAGVER                 | Flag table version to apply                                             |
| --primary   |      | SOURCE_1, [SOURCE_2, …] | Primary calibrator sources to use for clock and bandpass fringe fitting |
| --secondary |      | SOURCE_1, [SOURCE_2, …] | Secondary calibrator sources to use for atmospheric fringe fitting      |
| --refant    |      | REFANT                  | Primary reference antenna                                               |
| --search    |      | ANTENNA_1 [ANTENNA_2 …] | Secondary search antennas                                               |
| --clock_int |      | SOLINT                  | Clock delay solution interval in minutes (default: 5)                   |
| --clock_win |      | DELAY RATE              | Clock delay and rate windows in ns and MHz (default: 200, 200)          |
| --atmos_int |      | SOLINT                  | Atmospheric delay soliton interval in minutes (default: 5)              |
| --atmos_win |      | DELAY RATE              | Atmospheric delay and rate windows in ns and MHz (default: 100, 100)    |
| --bpass_int |      | SOLINT                  | Bandpass phase solution interval in minutes (default: 1)                |

Usage in this context: 

```
ParselTongue continuum_cal.py <user no> -m MASTR MSORT 1 1 -a AUXIL MSORT 1 1 -f 1 --primary NRAO530 --secondary J1752-29 --refant <reference antenna> --search <search antennas>
```

# Doppler Calculations

Sets the rest frequency of the observed maser line (water masers at 22.2350800 GHz), calculates velocities based on frequency, and shifts the visibility data to the target's local standard of rest (LSR).

**ParselTongue**

Syntax: 

```
ParselTongue doppler_calc.py USER_NO [-h] -m NAME CLASS SEQ DISK -r FREQ_1 FREQ_2 -s SOURCE_1 [SOURCE_2 ...] 
```

| Name       | Flag | Arguments               | Description                                           |
| ---------- | ---- | ----------------------- | ----------------------------------------------------- |
| USER_NO    |      |                         | AIPS user number                                      |
| --help     | -h   |                         | Displays help message                                 |
| --master   | -m   | NAME CLASS SEQ DISK     | Master catalogue information                          |
| --restfreq | -r   | FREQ_1 FREQ_2           | Rest frequency of spectral line (FREQ_1 + FREQ_2)     |
| --sources  | -s   | SOURCE_1, [SOURCE_2, …] | Sources to perform Doppler velocity calculations onto | 

Usage in this context:

```
ParselTongue doppler_calc.py <user no> -m MASTR MSORT 1 1 -r 2.223E+10 5080000 -s RCW142
```

# Maser Rate Calibration

Explanation goes here

**ParselTongue**

Syntax: 

```
ParselTongue maser_cal.py USER_NO [-h] -m NAME CLASS SEQ DISK [-f FLAGVER] -t SOURCE_1 [SOURCE_2 ...] -c CHANNEL --refant REFANT --search ANTENNA_1 [ANTENNA_2 ...] [--rate_int SOLINT] [--rate_win RATE]
```

| Name        | Flag | Arguments               | Description                                    |
| ----------- | ---- | ----------------------- | ---------------------------------------------- |
| USER_NO     |      |                         | AIPS user number                               |
| --help      | -h   |                         | Displays help message                          |
| --master    | -m   | NAME CLASS SEQ DISK     | Master catalogue information                   |
| --flagver   | -f   | FLAGVER                 | Flag table version to apply                    |
| --target    | -t   | SOURCE_1, [SOURCE_2, …] | Target maser sources to use for fringe fitting |
| --peak_chan | -c   | CHANNEL                 | Peak channel in maser spectrum                 |
| --refant    |      | REFANT                  | Primary reference antenna                      |
| --search    |      | ANTENNA_1 [ANTENNA_2 …] | Secondary search antennas                      |
| --rate_int  |      | SOLINT                  | Rate solution interval in minutes              |
| --rate_win  |      | RATE                    | Rate window in MHz                             |

Usage in this context: 

```
ParselTongue maser_cal.py <user no> -m MASTR MSORT 1 1 -f 1 -t RCW142 -c <peak channel> --refant <reference antenna> --search <search antennas>
```

***

# Self-Calibration

Explanation goes here

