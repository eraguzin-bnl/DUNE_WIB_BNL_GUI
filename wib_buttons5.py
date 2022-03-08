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
    
class WIBPowerConfButtons(QtWidgets.QGroupBox):
    def __init__(self,parent):
        super().__init__("Power Config")
        self.parent = parent
        button_grid = QtWidgets.QGridLayout()

        warning_label = QtWidgets.QLabel("Note that changing these settings will turn off any FEMBs that have been powered on. You will need to redo the Power Sequence!")
        warning_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        warning_label.setWordWrap(True)
        button_grid.addWidget(warning_label, 0, 0, 1, 5)
        
        reg_label = QtWidgets.QLabel("Regulator")
        reg_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(reg_label, 5, 0)

        value_label = QtWidgets.QLabel("Voltage (V)")
        value_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(value_label, 5, 1)

        dc1_label = QtWidgets.QLabel("DC-DC Converter 1")
        dc1_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(dc1_label, 6, 0)

        self.dc1_box = QtWidgets.QDoubleSpinBox()
        self.dc1_box.setMinimumWidth(60)
        self.dc1_box.setRange(0, 6)
        self.dc1_box.setSingleStep(0.01)
        self.dc1_box.setValue(4)
        self.dc1_box.setToolTip("Voltage for DC-DC 1 output")
        button_grid.addWidget(self.dc1_box, 6, 1)

        dc2_label = QtWidgets.QLabel("DC-DC Converter 2")
        dc2_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(dc2_label, 7, 0)

        self.dc2_box = QtWidgets.QDoubleSpinBox()
        self.dc2_box.setMinimumWidth(60)
        self.dc2_box.setRange(0, 6)
        self.dc2_box.setSingleStep(0.01)
        self.dc2_box.setValue(4)
        self.dc2_box.setToolTip("Voltage for DC-DC 2 output")
        button_grid.addWidget(self.dc2_box, 7, 1)

        dc3_label = QtWidgets.QLabel("DC-DC Converter 3")
        dc3_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(dc3_label, 8, 0)

        self.dc3_box = QtWidgets.QDoubleSpinBox()
        self.dc3_box.setMinimumWidth(60)
        self.dc3_box.setRange(0, 6)
        self.dc3_box.setSingleStep(0.01)
        self.dc3_box.setValue(4)
        self.dc3_box.setToolTip("Voltage for DC-DC 3 output")
        button_grid.addWidget(self.dc3_box, 8, 1)

        dc4_label = QtWidgets.QLabel("DC-DC Converter 4")
        dc4_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(dc4_label, 9, 0)

        self.dc4_box = QtWidgets.QDoubleSpinBox()
        self.dc4_box.setMinimumWidth(60)
        self.dc4_box.setRange(0, 6)
        self.dc4_box.setSingleStep(0.01)
        self.dc4_box.setValue(4)
        self.dc4_box.setToolTip("Voltage for DC-DC 4 output")
        button_grid.addWidget(self.dc4_box, 9, 1)

        ldo1_label = QtWidgets.QLabel("LDO Regulator 1")
        ldo1_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(ldo1_label, 10, 0)

        self.ldo1_box = QtWidgets.QDoubleSpinBox()
        self.ldo1_box.setMinimumWidth(60)
        self.ldo1_box.setRange(0, 6)
        self.ldo1_box.setSingleStep(0.01)
        self.ldo1_box.setValue(2.5)
        self.ldo1_box.setToolTip("Voltage for LDO 1 output")
        button_grid.addWidget(self.ldo1_box, 10, 1)

        ldo2_label = QtWidgets.QLabel("LDO Regulator 2")
        ldo2_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(ldo2_label, 11, 0)

        self.ldo2_box = QtWidgets.QDoubleSpinBox()
        self.ldo2_box.setMinimumWidth(60)
        self.ldo2_box.setRange(0, 6)
        self.ldo2_box.setSingleStep(0.01)
        self.ldo2_box.setValue(2.5)
        self.ldo2_box.setToolTip("Voltage for LDO 2 output")
        button_grid.addWidget(self.ldo2_box, 11, 1)

        write_button = QtWidgets.QPushButton('Write')
        write_button.setToolTip('Write the new regulator voltage outputs to the WIB. Will turn off the FEMBS!')
        write_button.clicked.connect(lambda: self.send_power_config())

        button_grid.addWidget(write_button, 12, 0, 1, 2)
        
        self.setLayout(button_grid)
        
    def send_power_config(self):
        req = wibpb.ConfigurePower()
        rep = wibpb.Status()
        req.dc2dc_o1 = self.dc1_box.value()
        req.dc2dc_o2 = self.dc2_box.value()
        req.dc2dc_o3 = self.dc3_box.value()
        req.dc2dc_o4 = self.dc4_box.value()
        req.ldo_a0 = self.ldo1_box.value()
        req.ldo_a1 = self.ldo2_box.value()
        if not self.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success:{rep.success}")
        
class WIBButtons5(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        layout.addWidget(WIBPowerConfButtons(self))
