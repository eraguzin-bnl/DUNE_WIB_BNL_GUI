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
    
class FEMBControlButtons(QtWidgets.QGroupBox):

        
    def enabled(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("Disabled")
        cb.addItem("Enabled")
        cb.setToolTip("Configuration will only apply to FEMBs that are enabled")
        if (self.first_run):
            cb.setCurrentIndex(1)
            self.first_run = False
        else:
            cb.setCurrentIndex(0)
        return cb
        
    def testcap(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("On")
        cb.addItem("Off")
        cb.setToolTip("Turn on the test capacitor in the LArASIC chips to allow test pulses")
        return cb
    
    def gain(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("4.7 mV/fC")
        cb.addItem("7.8 mV/fC")
        cb.addItem("14 mV/fC")
        cb.addItem("25 mV/fC")
        cb.setToolTip("Set the gain of the LArASIC")
        return cb
        
    def peaking_time(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("0.5 us")
        cb.addItem("1 us")
        cb.addItem("2 us")
        cb.addItem("3 us")
        return cb
        
    def baseline(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("200 mV")
        cb.addItem("900 mV")
        cb.setToolTip("Set the baseline of the LArASIC")
        return cb
        
    def dac(self):
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 0x3F)
        sb.setDisplayIntegerBase(16)
        font = sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        sb.setFont(font)
        sb.setToolTip("Internal DAC value for LArASIC test pulses")
        return sb
    
    def leakage(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("100 pA")
        cb.addItem("500 pA")
        cb.addItem("1 nA")
        cb.addItem("5 nA")
        cb.setToolTip("Set the leakage current of the LArASIC")
        return cb
        
    def coupling(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("AC")
        cb.addItem("DC")
        cb.setToolTip("Set the coupling of the LArASIC")
        return cb
        
    def buffer(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("Off")
        cb.addItem("On")
        cb.setToolTip("Turn the LArASIC buffer on or off")
        return cb
        
    def strobe_skip(self):
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 0xFFFFFFF)
        sb.setDisplayIntegerBase(16)
        font = sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        sb.setFont(font)
        sb.setToolTip("Test pulse - 2MHz periods to skip after strobe")
        return sb
        
    def strobe_delay(self):
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 0xFFFFFFF)
        sb.setDisplayIntegerBase(16)
        font = sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        sb.setFont(font)
        sb.setToolTip("Test pulse - offset from 2MHz to start strobe in 64MHz periods")
        return sb
        
    def strobe_length(self):
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 0xFFFFFFF)
        sb.setDisplayIntegerBase(16)
        font = sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        sb.setFont(font)
        sb.setToolTip("Test pulse - length of strobe in 64MHz periods")
        return sb
        
    def __init__(self,parent):
        super().__init__("FEMB Control",parent)
        self.parent = parent
        button_grid = QtWidgets.QGridLayout()
        fembs = 4
        self.first_run = True
        femb_settings = [
                ["Enable", self.enabled],
                ["Test Cap", self.testcap],
                ["Gain", self.gain],
                ["Peaking Time", self.peaking_time],
                ["Baseline", self.baseline],
                ["Pulse DAC", self.dac],
                ["Leakage Current", self.leakage],
                ["Coupling", self.coupling],
                ["Differential Buffer", self.buffer],
                ["Strobe Skip", self.strobe_skip],
                ["Strobe Delay", self.strobe_delay],
                ["Strobe Length", self.strobe_length]]
        
        for num, i in enumerate(femb_settings):
            label = QtWidgets.QLabel(i[0])
            button_grid.addWidget(label, 1+num, 0)
            
        all_widgets = [[],[],[],[]]
        for i in range(fembs):
            label = QtWidgets.QLabel(f"FEMB {i}")
            button_grid.addWidget(label, 0, 1+i)
            for num,j in enumerate(femb_settings):
                widget = j[1]()
                button_grid.addWidget(widget, 1+num, 1+i)
                all_widgets[i].append(widget)
        print(all_widgets)
        self.setLayout(button_grid)
        
class WIBButtons4(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        layout.addWidget(FEMBControlButtons(self))
