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
    
class PowerButtons(QtWidgets.QGroupBox):
    def __init__(self,parent):
        super().__init__('Power on sequence',parent)
        self.parent = parent
        button_grid = QtWidgets.QGridLayout()
        self.power_buttons = []
        for i in range(4):
            check_box = QtWidgets.QCheckBox(f"FEMB {i}")
            if (i == 0):
                check_box.setChecked(True)
            else:
                check_box.setChecked(False)
            button_grid.addWidget(check_box, i, 1)
            self.power_buttons.append(check_box)
            
        cold_checkbox = QtWidgets.QCheckBox("Cold Config")
        cold_checkbox.setChecked(False)
        button_grid.addWidget(cold_checkbox, 1, 0)
        self.power_buttons.append(cold_checkbox)
        
        power_button = QtWidgets.QPushButton('Power On/Connect')
        power_button.setToolTip('Initial connection and power on with the WIB')
        power_button.clicked.connect(self.power_on)
        
        status_button = QtWidgets.QPushButton('WIB Version')
        status_button.setToolTip('Check onboard WIB Software Version')
        status_button.clicked.connect(self.status)
        
        button_grid.addWidget(power_button, 0, 0)
        button_grid.addWidget(status_button, 4, 0)
        
        self.setLayout(button_grid)
        
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
        self.parent.print_gui("Powering on WIB with full power sequence")
        sys.stdout.flush()
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui(rep.extra.decode('ascii'))
        self.parent.print_gui("Successful:{}".format(rep.success))
        
    @QtCore.pyqtSlot()
    def status(self):
        req = wibpb.GetSWVersion()
        rep = wibpb.GetSWVersion.Version()
        self.parent.print_gui("Getting Status")
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui('sw_version: %s'%rep.version);

class WIBButtons1(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        
        power_gb = PowerButtons(self)
        
        layout.addWidget(power_gb)
