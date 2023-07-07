# RCW 142 KaVA Data Reduction

## Progress Summary

* 5 epochs downloaded, all can be loaded to AIPS with no issues.
* Currently calibrating 1st epoch
* Amplitude calibration is fine, but phase calibration (dummy+instrumental) doesn't look good. NRAO 530 image seems realistic, but RCW 142 phase looks relatively scattered.
* Continuing with phase+rate calibration (line) using brightest peak (channel 476) also doesn't give good results i.e. no fringes found when using FRMAP.

## Data Reduction Procedure

[AIPS Reduction procedure](reduction_procedure.md)

[Reference AIPS log for AFGL 5142](aips_log.old.txt)

## Epochs

| Experiment Code | Bucket | Start Date | End Date | Start Time | End Time | Velocity (km/s) |
| --- | --- | --- | --- | --- | --- | --- |
| k18th01h | r18282a | October 9, 2018 | October 9, 2018 | 03:45:00 | 11:15:00 | 212.4570 |
| k18th01m | r18330a | November 26, 2018 | November 26, 2018 | 00:45:00 | 08:15:00 | 228.4740 |
| k18th01q | r19017b | January 17, 2019 | January 18, 2019 | 21:10:00 | 05:15:00 | 255.2704 |
| k19th04b | r19073c | March 14, 2019 | March 15, 2019 | 17:30:00 | 01:30:00 | 256.8041 |
| k19th04c | r19129b | May 9, 2019 | May 9, 2019 | 13:36:00 | 21:16:00 | 246.0630 |

---

## Progress Details

* [K18TH01H](k18th01h.md)
* [K18TH01M](k18th01m.md)
* [K18TH01Q](k18th01q.md)
* [K19TH04B](k19th04b.md)
* [K19TH04C](k19th04c.md)
