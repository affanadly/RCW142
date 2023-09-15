# RCW 142 AIPS Data Reduction Procedure

## Catalogue Descriptions

1. MULTI.MSORT.1: Multi-source UV data, sorted
    * General tables: HI1, AT1, CT1, FQ1, AN1, SU1, NX1, GC1, TY1
    * Solution tables:
        * SN1: ACCOR solution
        * SN2: Modified ACCOR solution
        * SN3: ANTAB/APCAL solution
        * SN4: NRAO530 FRING delay solution for NRAO530
        * SN5: NRAO530 FRING delay solution for RCW142
    * Calibration tables:
        * CL1: Empty calibration table
        * CL2: Contains modified ACCOR solution (SN2)
        * CL3: Contains CL2 and ANTAB/APCAL solution (SN3)
        * CL4: Contains CL3 and NRAO530 FRING delay solution for NRAO530 (SN4)
        * CL5: Contains CL3 and NRAO530 FRING delay solution for RCW142 (SN5)
        * CL6: Contains CL5 with shifted phase-tracking center coordinates
    * Bandpass tables:
        * BP1: Bandpass table obtained using NRAO530
2. NRAO530.SPLAT.1: NRAO530 UV data with CL4 solution in Cat 2
    * General tables: HI1, AT1, CT1, FQ1, AN1, SU1, NX1, GC1, TY1
    * Calibration tables:
        * CL1: Empty calibration table
3. NRAO530.IBM001.1: Dirty image of NRAO530
4. NRAO530.ICL001.1: Clean image of NRAO530
5. MULTI.CVEL.1: Multi-source UV data, sorted, Doppler shifted (with tables from Cat 1)
    * Solution tables:
        * SN6: RCW142 FRING rate solution for RCW142
    * Calibration tables:
        * CL7: Contains CL6 and RCW142 FRING rate solution for RCW142 (SN6)

## Loading data

* FITLD: Load .fits file as a catalogue, Creates Catalogue 1

    ```plain
    task 'fitld'; default
    datain 'PWD:<fits file>
    clint 1.6384/60
    digicor -1
    go
    recat
    ```

* MSORT: Sort data by time, Creates Catalogue 2 with tables from Cat 1 but sorted visibilities

    ```plain
    task 'msort'; default
    getn 1
    go
    ```

* ZAP: Delete scrap catalogue, Deletes Catalogue 1 and renumbers Cat 2 as Cat 1

    ```plain
    getn 1
    zap
    recat
    ```

* INDXR: Index UV data and creates an empty calibration table, Creates CL1 and NX1 for Cat 1

    ```plain
    task 'indxr'; default
    getn 1
    cparm(3) 1.6384/60
    go
    ```

## Amplitude Calibration

### Correcting Sampler Errors

* ACCOR: Correct sampler errors in cross-correlation using auto-correlation data, Creates SN1 for Cat 1

    ```plain
    task 'accor'; default
    getn 1
    solint 1.6384/60
    go
    ```

* SNEDT: Edit solution table to remove anomalous solutions, Creates SN2 for Cat 1

    ```plain
    task 'snedt'; default
    getn 1
    inext 'sn'
    inver 1
    solint 1.6384/60
    go
    ```

* CLCAL: Combine previous calibration with solution table, Creates CL2 for Cat 1

    ```plain
    task 'clcal'; default
    getn 1
    opcode 'cali'
    interpol 'self'
    smotype 'ampl'
    snver 2
    inver 2
    gainver 1
    gainuse 2
    refant -1
    go
    ```

### Antenna Gain and Temperature Calibrations

* ANTAB: Load antennae temperature data, Creates GC1 and TY1 for Cat 1

    ```plain
    task 'antab'; default
    getn 1
    calin 'PWD:<antab file>
    go
    ```

* APCAL: Generate amplitude solution from antenna temperature data, Creates SN3/2 for Cat 1

    ```plain
    task 'apcal'; default
    getn 1
    solint 3
    go
    ```

* CLCAL: Combine previous calibration with solution table, Creates CL3 for Cat 1

    ```plain
    task 'clcal'; default
    getn 1
    interpol '2pt'
    samptype 'box'
    bparm(1) 3/60
    snver 3
    inver 3
    gainver 2
    gainuse 3
    refant -1
    go
    ```

### Bandpass Calibration

* BPASS: Generate bandpass table from calibrator source, Creates BP1 for Cat 1

    ```plain
    task 'bpass'; default
    getn 1
    bpassprm 1 0
    docal 0
    solint -1
    calsour 'NRAO530''
    go
    ```
