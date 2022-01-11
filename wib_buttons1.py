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

class WIBButtons1(QtWidgets.QWidget):
    def __init__(self, wib=None, text=None):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.text = text
        layout = QtWidgets.QVBoxLayout(self)
        
        button_layout_top = QtWidgets.QHBoxLayout()
        
        button = QtWidgets.QPushButton('Power On/Connect')
        button_layout_top.addWidget(button)
        button.setToolTip('Initial connection and power on with the WIB')
        button.clicked.connect(self.power_on)
        
        button2 = QtWidgets.QPushButton('Status')
        button_layout_top.addWidget(button2)
        button2.setToolTip('Check status')
        button2.clicked.connect(self.status)
        
        layout.addLayout(button_layout_top)
    @QtCore.pyqtSlot()
    def power_on(self):
        req = wibpb.PowerWIB()
        req.femb0 = True
        req.femb1 = False
        req.femb2 = False
        req.femb3 = False
        req.cold = False
        req.stage = 0
        rep = wibpb.Status()
        self.text.append("Powering on WIB with full power sequence")
        self.wib.send_command(req,rep)
        self.text.append(rep.extra.decode('ascii'))
        self.text.append('Successful:',rep.success)
        
    @QtCore.pyqtSlot()
    def status(self):
        req = wibpb.GetSWVersion()
        rep = wibpb.GetSWVersion.Version()
        self.text.append("Getting Status")
        self.wib.send_command(req,rep)
        self.text.append('sw_version: %s'%rep.version);