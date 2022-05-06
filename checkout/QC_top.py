# -*- coding: utf-8 -*-
"""
File Name: cls_udp.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/20/2019 4:52:43 PM
Last modified: 4/21/2022 2:35:44 PM
"""

import numpy as np
import sys
import os
import string
import time
#from datetime import datetime
from QC_runs import QC_runs

tm = int(sys.argv[1])

qc = QC_runs()
times = []
times.append(time.time())

if tm == 1:
    qc.FEMB_CHKOUT_Input()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 2:
    qc.load_logs()
    qc.femb_initpwr_chk()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 3:
    qc.load_logs()
    qc.femb_pwr_meas()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 4:
    qc.load_logs()
    qc.femb_pwr_cycles()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 5:
    qc.load_logs()
    qc.femb_chks()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 6:
    qc.load_logs()
    qc.femb_rmss()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 7:
    qc.load_logs()
    qc.femb_asicdac_calis()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 8:
    qc.load_logs()
    qc.femb_mons()
    times.append(time.time())
    qc.dump_logs(tm=tm)
    times.append(time.time())

if tm == 9:
    qc.load_logs()
    qc.close()
    times.append(time.time())

for dt in range (len(times)):
    if dt >=1:
        print (time.ctime(times[dt]), int(times[dt] - times[dt-1]))
    else:
        print (time.ctime(times[dt]))

