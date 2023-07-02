# RCW 142 KaVA Data Reduction

## Progress Summary

* 5 epochs downloaded, all can be loaded to AIPS with no issues.
* Currently calibrating 1st epoch
* Amplitude calibration is fine, but phase calibration (dummy+instrumental) doesn't look good. NRAO 530 image seems realistic, but RCW 142 phase looks relatively scattered.
* Continuing with phase+rate calibration (line) using brightest peak (channel 476) also doesn't give good results i.e. no fringes found when using FRMAP.

## Data Reduction Procedure

[AIPS Reduction procedure](reduction_procedure.md)
[Reference AIPS log for AFGL 1542](aips_log.old.txt)

## Epochs

| Experiment Code | Bucket | Start Date | End Date | Start Time | End Time | Velocity (km/s) |
| --- | --- | --- | --- | --- | --- | --- |
| k18th01h | r18282a | October 9, 2018 | October 9, 2018 | 03:45:00 | 11:15:00 | 212.4570 |
| k18th01m | r18330a | November 26, 2018 | November 26, 2018 | 00:45:00 | 08:15:00 | 228.4740 |
| k18th01q | r19017b | January 17, 2019 | January 18, 2019 | 21:10:00 | 05:15:00 | 255.2704 |
| k19th04b | r19073c | March 14, 2019 | March 15, 2019 | 17:30:00 | 01:30:00 | 256.8041 |
| k19th04c | r19129b | May 9, 2019 | May 9, 2019 | 13:36:00 | 21:16:00 | 246.0630 |

---

## Details (K18TH01H)

### RCW 142 Pre-FRING (Amplitude calibration complete) results

* Baseline-averaged auto-correlation
![prefring ba auto](Resources/prefring_ba_auto.png)
* Baseline-averaged cross-correlation
![prefring ba cross](Resources/prefring_ba_cross.png)
* Per-baseline cross-correlation
![prefring pb cross](Resources/prefring_pb_cross_1a.png)
![prefring pb cross](Resources/prefring_pb_cross_1b.png)
![prefring pb cross](Resources/prefring_pb_cross_1c.png)
![prefring pb cross](Resources/prefring_pb_cross_2a.png)
![prefring pb cross](Resources/prefring_pb_cross_2b.png)
![prefring pb cross](Resources/prefring_pb_cross_2c.png)

### Preliminary phase calibration (dummy+instrumental) results

* NRAO 530 image
![nrao530](Resources/predi_nrao530.png)
* Baseline-averaged cross-correlation
![predi ba cross](Resources/predi_ba_cross.png)
* Per-baseline cross-correlation
![predi pb cross](Resources/predi_pb_cross_1a.png)
![predi pb cross](Resources/predi_pb_cross_1b.png)
![predi pb cross](Resources/predi_pb_cross_2a.png)
![predi pb cross](Resources/predi_pb_cross_2b.png)

Peaks found:

1. Channel 476: Brightest, ~180 Jy
2. Channel 464: Second brightest, ~120 Jy
3. Channel 470: Between two brightest components, ~80 Jy
4. Channel 389: One of pair peaks, third brightest, ~95 Jy
5. Channel 327: One of pair peaks, third brightest, ~95 Jy
6. Channel 357: Between pair peaks, weakest single peak emission, ~75 Jy

* Visibility-time plots
  * Channel 476
![uv 476](Resources/uv_476_a1.png)
![uv 476](Resources/uv_476_a2.png)
![uv 476](Resources/uv_476_p1.png)
![uv 476](Resources/uv_476_p2.png)
  * Channel 464
![uv 464](Resources/uv_464_a1.png)
![uv 464](Resources/uv_464_a2.png)
![uv 464](Resources/uv_464_p1.png)
![uv 464](Resources/uv_464_p2.png)
  * Channel 470
![uv 470](Resources/uv_470_a1.png)
![uv 470](Resources/uv_470_a2.png)
![uv 470](Resources/uv_470_p1.png)
![uv 470](Resources/uv_470_p2.png)
  * Channel 389
![uv 389](Resources/uv_389_a1.png)
![uv 389](Resources/uv_389_a2.png)
![uv 389](Resources/uv_389_p1.png)
![uv 389](Resources/uv_389_p2.png)
  * Channel 327
![uv 327](Resources/uv_327_a1.png)
![uv 327](Resources/uv_327_a2.png)
![uv 327](Resources/uv_327_p1.png)
![uv 327](Resources/uv_327_p2.png)
  * Channel 357
![uv 357](Resources/uv_357_a1.png)
![uv 357](Resources/uv_357_a2.png)
![uv 357](Resources/uv_357_p1.png)
![uv 357](Resources/uv_357_p2.png)

### Preliminary phase+rate calibration (line) results

* Baseline-averaged cross-correlation
![preline ba cross](Resources/preline_ba_cross.png)
* Per-baseline cross-correlation
![preline pb cross](Resources/preline_pb_cross_1a.png)
![preline pb cross](Resources/preline_pb_cross_1b.png)
![preline pb cross](Resources/preline_pb_cross_2a.png)
![preline pb cross](Resources/preline_pb_cross_2b.png)
