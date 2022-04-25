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
            
        cold_checkbox = QtWidgets.QCheckBox("Cold Configuration")
        cold_checkbox.setToolTip('Check to configure WIB with cold settings')
        cold_checkbox.setChecked(False)
        button_grid.addWidget(cold_checkbox, 1, 0)
        self.power_buttons.append(cold_checkbox)
        
        self.power_sequence_box = QtWidgets.QComboBox(self)
        self.power_sequence_box.setToolTip('Different power on sequences:\n'
                                 '1: Full Power On Sequence (run this one when in doubt)\n'
                                 '2: Leave VDDD and VDDA off, COLDATA needing reset, waiting for a '
                                 'global ACT signal\n'
                                 '3: Resume the power on sequence')
        self.power_sequence_box.addItem("Power Sequence 1")
        self.power_sequence_box.addItem("Power Sequence 2")
        self.power_sequence_box.addItem("Power Sequence 3")
        button_grid.addWidget(self.power_sequence_box, 2, 0)
        
        power_button = QtWidgets.QPushButton('Power On/Connect')
        power_button.setToolTip('Initial connection and power on with the WIB')
        power_button.clicked.connect(self.power_on)
        

        button_grid.addWidget(power_button, 0, 0)
        
        self.setLayout(button_grid)

        
    def get_sequence_box(self):
        return self.power_sequence_box.currentIndex()
        
    @QtCore.pyqtSlot()
    def power_on(self):
        req = wibpb.PowerWIB()
        req.femb0 = self.power_buttons[0].checkState()
        req.femb1 = self.power_buttons[1].checkState()
        req.femb2 = self.power_buttons[2].checkState()
        req.femb3 = self.power_buttons[3].checkState()
        req.cold = self.power_buttons[4].checkState()
        req.stage = self.get_sequence_box()
        rep = wibpb.Status()
        if (req.stage == 0):
            self.parent.print_gui("Powering on WIB with full power sequence...")
        elif (req.stage == 1):
            self.parent.print_gui("Powering on WIB, leaving VDDD and VDDA off, "
                                  "COLDATA needing reset, will wait for a global ACT signal")
        elif (req.stage == 2):
            self.parent.print_gui("Resuming power ON after external COLDADC reset and synchronization")
        else:
            self.parent.print_gui("Error: Somehow an impossible choice was made in the power stage box")
            return 0
        sys.stdout.flush()
        if not self.parent.wib.send_command(req,rep, self.parent.print_gui):
            self.parent.print_gui(rep.extra.decode('ascii'))
            self.parent.print_gui(f"Successful:{rep.success}")


class WIBButtons1(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        
        self.power_gb = PowerButtons(self)
        
        layout.addWidget(self.power_gb)
