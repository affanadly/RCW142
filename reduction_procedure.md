# RCW 142 KaVA AIPS Data Reduction Procedure

1. MULTI.MSORT.1: Multi-source UV data, sorted
    * General tables: HI1, AT1, CT1, FQ1, AN1, SU1, NX1, GC1, TY1
    * Solution tables:
      * SN1: ACCOR solution
      * SN2: Modified ACCOR solution
      * SN3: ANTAB/APCAL solution
      * SN4: NRAO530 FRING solution for NRAO530
      * SN5: NRAO530 FRING solution for RCW142
      * SN6: RCW142 FRING solution for RCW142
    * Calibration tables:
      * CL1: Empty calibration table
      * CL2: Contains modified ACCOR solution (SN2)
      * CL3: Contains CL2 and ANTAB/APCAL solution (SN3)
      * CL4: Contains CL3 and NRAO530 FRING solution for NRAO530 (SN4)
      * CL5: Contains CL3 and NRAO530 FRING solution for RCW142 (SN5)
      * CL6: Contains CL5 and RCW142 FRING solution for RCW142 (SN6)
    * Bandpass tables:
      * BP1: Bandpass table obtained using NRAO530
2. NRAO530.SPLAT.1: NRAO530 UV data with CL4 solution in Cat 2
    * General tables: HI1, AT1, CT1, FQ1, AN1, SU1, NX1, GC1, TY1
    * Calibration tables:
      * CL1: Empty calibration table
3. NRAO530.IBM001.1: Dirty image of NRAO530
4. NRAO530.ICL001.1: Clean image of NRAO530
5. MULTI.CVEL.1: Velocity shifted multi-source UV data with tables copied from Cat 2
6. MULTI.TASAV.1: Dummy catalogue with all tables from Cat 5
7. RCW142.SPLAT.1: RCW142 UV data with CL6 solution in Cat 5
    * General tables: HI1, CT1, FQ1, AN1, SU1, NX1, GC1, TY1
    * Calibration tables:
      * CL1: Empty calibration table
    * Bandpass tables:
      * BP1: Bandpass table obtained using NRAO530

## Loading data

* FITLD (Creates a catalogue item from a fits file)
  * Creates Catalogue 1

  ```plain
  task 'fitld'; default
  datain 'PWD:<fits file>
  clint 1.6384/60
  digicor -1
  go
  recat
  ```

* MSORT (Sorts the visibilities)
  * Creates Catalogue 2 with tables from Cat 1 but sorted visibilities

  ```plain
  task 'msort'; default
  getn 1
  go
  ```

* ZAP (Deletes catalogue)
  * Deletes Catalogue 1 (scratch file), and renumbers Cat 2 as Cat 1

  ```plain
  getn 1
  zap
  recat
  ```

* INDXR (Creates an index table)
  * Creates CL1 and NX1 for Cat 1

  ```plain
  task 'indxr'; default
  getn 2
  cparm(3) 1.6384/60
  go
  ```

## Amplitude Calibration

### Correcting cross-correlation

* ACCOR (Corrects the cross-correlation spectra using auto-correlation)
  * Creates SN1 for Cat 1

  ```plain
  task 'accor'; default
  getn 1
  solint 1.6384/60
  go
  ```

* SNEDT (Manually remove anomalous solutions if necessary)
  * Creates SN2 for Cat 1

  ```plain
  task 'snedt'; default
  getn 1
  inext 'sn'
  inver 1
  solint 1.6384/60
  go
  ```

* CLCAL (Create calibration table with modified ACCOR solution)
  * Creates CL2 for Cat 1

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

* ANTAB (Load antenna gain and temperatures from ANTAB file)
  * Creates GC1 and TY1 for Cat 1

  ```plain
  task 'antab'; default
  getn 1
  calin 'PWD:<antab file>
  go
  ```

* APCAL (Creates solution table using ANTAB data)
  * Creates SN3 for Cat 1

  ```plain
  task 'apcal'; default
  getn 1
  solint 3
  go
  ```

* CLCAL (Create calibration table with CL1 and ANTAB/APCAL solution)
  * Creates CL3 for Cat 1

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

* BPASS (Create bandpass calibration table using NRAO530 as continuum calibrator)
  * Creates BP1 for Cat 1

  ```plain
  task 'bpass'; default
  getn 1
  bpassprm 1 0
  docal 0
  solint -1
  calsour 'NRAO530''
  go
  ```

---

> The procedure below this line seems problematic

## Phase Calibration

### Fringe Fitting with Continuum (Dummy)

* FRING (Create solution table for NRAO530 based on fringe fitting of NRAO530)
  * Creates SN4 for Cat 1

  ```plain
  task 'fring'; default
  getn 1
  docal 1
  gainuse 3
  doband -1
  refant 2
  search 5
  aparm 2,-1,0,0,0,0,5,0,1
  dparm 1,200,300,1
  calsour 'NRAO530''
  solint 1
  solsub 0
  go
  ```

* CLCAL (Create calibration table with CL3 and NRAO530 FRING solution for NRAO530)
  * Creates CL4 for Cat 1

  ```plain
  task 'clcal'; default
  getn 1
  calcode ''
  opcode 'cali'
  soucode ''
  smotype 'full'
  samptype '2pth'
  dobtween 1
  bparm(4) 1
  refant 2
  calsour 'NRAO530''
  sources 'NRAO530''
  snver 4
  gainver 3
  gainuse 4
  go
  ```

* SPLAT (Splits NRAO530 into a catalogue with NRAO530 FRING solution)
  * Creates Catalogue 2 only with NRAO530 and calibrations from Cat 1 (CL4)

  ```plain
  task 'splat'; default
  getn 1
  docal 1
  gainuse 4
  sources 'NRAO530''
  outname 'NRAO530
  aparm(1) 1
  go
  ```

* IMAGR (Obtain image of NRAO530)
  * Creates Catalogue 3 with dirty image of NRAO530 and Catalogue 4 with clean image of NRAO530

  ```plain
  task 'imagr'; default
  getn 2
  nchav 0
  minpatch 128
  onebeam -1
  maxpixel 0
  cellsize 0.0001 0.0001
  imsize 1024 1024
  dotv -1
  niter 500
  robust 0
  stokes 'I'
  docal -1
  srcname 'NRAO530'
  go
  recat
  ```

### Fringe Fitting with Continuum (Instrumental)

* FRING (Create solution table for RCW142 based on fringe fitting of NRAO530)
  * Creates SN5 for Cat 1

  ```plain
  task 'fring'; default
  getn 1
  docal 1
  gainuse 3
  doband -1
  refant 2
  search 5
  aparm 2,-1,0,0,0,0,7,0,1
  dparm 1,300,100,1,0,0,0,1
  calsour 'NRAO530''
  solint 10
  solsub 0
  go
  ```

* CLCAL (Create calibration table with CL5 and NRAO530 FRING solution for RCW142)
  * Creates CL5 for Cat 1

  ```plain
  task 'clcal'; default
  getn 1
  calcode ''
  opcode 'cali'
  soucode ''
  smotype 'full'
  samptype '2pth'
  dobtween 1
  bparm(4) 1
  refant 2
  calsour 'NRAO530''
  sources ''
  snver 5
  gainver 3
  gainuse 5
  go
  ```

### Fringe Fitting with Maser (Line)

* FRING (Create solution table for RCW142 based on fringe fitting of RCW142)
  * Creates SN6 for Cat 1

  ```plain
  task 'fring'; default
  getn 1
  aparm 2,0,-1,0,0,0,3,0,1
  dparm 0,-1,200
  refant 2
  calsour 'RCW142''
  docal 1
  gainuse 5
  doband -1
  bchan 476
  echan 476
  solint 0.0625
  go
  ```

* CLCAL (Create calibration table with CL5 and RCW142 FRING solution for RCW142)
  * Creates CL6 for Cat 1

  ```plain
  task 'clcal'; default
  getn 1
  opcode 'cali'
  interpol 'ambg'
  refant 2
  calsour 'RCW142''
  sources 'RCW142''
  snver 6
  gainver 5
  gainuse 6
  go
  ```

## Set Transition Frequency and Velocity Shift

* SETJY (Adding velocity/frequency information to SU table)
  * Modifies SU1 for Cat 1

  ```plain
  task 'setjy'; default
  getn 1
  restfreq 2.223E+10, 5080000
  veltyp 'lsr'
  veldef 'radio'
  optype 'vcal'
  sources 'RCW142''
  go
  ```

* CVEL (Shifts spectral line to a velocity)
  * Creates Catalogue 5 with shifted velocities/frequencies from Cat 1

  ```plain
  task 'cvel'; default
  getn 1
  aparm(10) 1
  aparm(4) 1
  freqid 1
  sources 'RCW142''
  gainuse 6
  go
  ```

## Finalizing Calibrations

* TASAV (Creates a dummy catalogue with all tables from Cat 1)
  * Creates Catalogue 6 with all tables from Cat 1

  ```plain
  task 'tasav'; default
  getn 5
  go
  ```

* SPLAT (Splits RCW142 into a catalogue with all calibrations)
  * Creates Catalogue 7 only with RCW142 and calibration from Cat 6 (CL6)

  ```plain
  task 'splat'; default
  getn 5
  docal 1
  gainuse 6
  doband -1
  aparm(5) 1
  sources 'RCW142''
  outname 'RCW142
  go
  ```
