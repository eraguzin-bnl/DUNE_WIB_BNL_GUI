#!/usr/bin/env python3

import os
import sys
import time
import pickle
import argparse
import numpy as np
from collections import deque

from wib import WIB
import wib_pb2 as wibpb

try:
    from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui
except:
    from matplotlib.backends.backend_qt4agg import QtCore, QtWidgets, QtGui
    
class WIBClientButtons(QtWidgets.QGroupBox):
    def __init__(self,parent):
        super().__init__('WIB Client',parent)
        self.parent = parent
        button_grid = QtWidgets.QGridLayout()
        
        reboot_button = QtWidgets.QPushButton('Reboot WIB')
        reboot_button.setToolTip('Restart the WIB software')
        reboot_button.clicked.connect(self.reboot)
        
        log_button = QtWidgets.QPushButton('Log Function')
        log_button.setToolTip('Execute Log Function in drop down box')
        log_button.clicked.connect(self.log)
        
        self.logBox = QtWidgets.QComboBox(self)
        self.logBox.addItem("Return Regular Log")
        self.logBox.addItem("Return Boot Log")
        self.logBox.addItem("Clear Log")
        
        timestamp_button = QtWidgets.QPushButton('WIB Timestamp')
        timestamp_button.setToolTip('Return firmware version timestamp')
        timestamp_button.clicked.connect(self.fw_timestamp)
        
        status_button = QtWidgets.QPushButton('WIB SW Version')
        status_button.setToolTip('Return software build version')
        status_button.clicked.connect(self.sw_status)
        
        treset_button = QtWidgets.QPushButton('Timing Endpoint Reset')
        treset_button.setToolTip('Reset the timing endpoint')
        treset_button.clicked.connect(self.timing_reset)
        
        tstatus_button = QtWidgets.QPushButton('Timing Status')
        tstatus_button.setToolTip('Return the status of the timing endpoint')
        tstatus_button.clicked.connect(self.timing_status)
        
        button_grid.addWidget(self.logBox, 0, 0)
        button_grid.addWidget(log_button, 0, 1)
        button_grid.addWidget(reboot_button, 1, 0)
        button_grid.addWidget(timestamp_button, 1, 1)
        button_grid.addWidget(status_button, 2, 0)
        button_grid.addWidget(treset_button, 2, 1)
        button_grid.addWidget(tstatus_button, 3, 0)
        
        self.setLayout(button_grid)
        
    def get_log_box(self):
        return self.logBox.currentIndex()
        
    @QtCore.pyqtSlot()
    def reboot(self):
        req = wibpb.Reboot()
        rep = wibpb.Empty()
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui('Rebooting...')
        
    @QtCore.pyqtSlot()
    def log(self):
        req = wibpb.LogControl()
        log_options = self.get_log_box()
        if (log_options == 0):
            req.return_log = True
            req.boot_log = False
            req.clear_log = False
            self.parent.print_gui("Getting Log...")
        elif (log_options == 1):
            req.return_log = False
            req.boot_log = True
            req.clear_log = False
            self.parent.print_gui("Getting Boot Log...")
        elif (log_options == 2):
            req.return_log = False
            req.boot_log = False
            req.clear_log = True
            self.parent.print_gui("Clearing Log...")
        else:
            self.parent.print_gui("Error: Somehow an impossible choice was made in the log box")
            return 0
        rep = wibpb.LogControl.Log()
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui(rep.contents.decode('ascii'),end='')
        
    @QtCore.pyqtSlot()
    def fw_timestamp(self):
        req = wibpb.GetTimestamp()
        rep = wibpb.GetTimestamp.Timestamp()
        self.parent.print_gui("Getting Firmware Timestamp...")
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui('Firmware Timestamp Code: 0x%08X'%rep.timestamp);
        self.parent.print_gui('decoded: %i/%i/%i %i:%i:%i'%(rep.year,
                                                            rep.month,rep.day,rep.hour,rep.min,rep.sec));
        
    @QtCore.pyqtSlot()
    def sw_status(self):
        req = wibpb.GetSWVersion()
        rep = wibpb.GetSWVersion.Version()
        self.parent.print_gui("Getting Status...")
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui(f"Software Version: {rep.version}")
        
    @QtCore.pyqtSlot()
    def timing_reset(self):
        req = wibpb.ResetTiming()
        rep = wibpb.GetTimingStatus.TimingStatus()
        self.parent.wib.send_command(req,rep)
        self.print_timing_status(rep)
        
    @QtCore.pyqtSlot()
    def timing_status(self):
        req = wibpb.GetTimingStatus()
        rep = wibpb.GetTimingStatus.TimingStatus()
        self.parent.wib.send_command(req,rep)
        self.print_timing_status(rep)
        
    def print_timing_status(self,timing_status):
        self.parent.print_gui('--- PLL INFO ---')
        self.parent.print_gui('LOS:         0x%x'%(timing_status.los_val & 0x0f))
        self.parent.print_gui('OOF:         0x%x'%(timing_status.los_val >> 4))
        self.parent.print_gui('LOS FLG:     0x%x'%(timing_status.los_flg_val & 0x0f))
        self.parent.print_gui('OOF FLG:     0x%x'%(timing_status.los_flg_val >> 4))
        self.parent.print_gui('HOLD:        0x%x'%( (timing_status.los_val >> 5) & 0x1 ))
        self.parent.print_gui('LOL:         0x%x'%( (timing_status.los_val >> 1) & 0x1 ))
        self.parent.print_gui('HOLD FLG:    0x%x'%( (timing_status.lol_flg_val >> 5) & 0x1 ))
        self.parent.print_gui('LOL FLG:     0x%x'%( (timing_status.lol_flg_val >> 1) & 0x1 ))
        self.parent.print_gui('--- EPT INFO ---')
        self.parent.print_gui('EPT CDR LOS: 0x%x'%( (timing_status.ept_status >> 17) & 0x1 )) # bit 17 is CDR LOS as seen by endpoint
        self.parent.print_gui('EPT CDR LOL: 0x%x'%( (timing_status.ept_status >> 16) & 0x1 )) # bit 16 is CDR LOL as seen by endpoint
        self.parent.print_gui('EPT TS RDY:  0x%x'%( (timing_status.ept_status >> 8 ) & 0x1 )) # bit 8 is ts ready
        self.parent.print_gui('EPT STATE:   0x%x'%(  timing_status.ept_status & 0x0f )) # bits 3:0 are the endpoint state

class WIBButtons2(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        wib_client_buttons = WIBClientButtons(self)
        layout.addWidget(wib_client_buttons)