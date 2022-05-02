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
    
class WIBScript(QtWidgets.QGroupBox):
    def __init__(self,parent):
        super().__init__("Scripts")
        self.parent = parent
        #fast_cmds = { 'reset':1, 'act':2, 'sync':4, 'edge':8, 'idle':16, 'edge_act':32 }
        self.script_dict = {0:"conf_pll_timing", 1:"cdr_reset", 2:"pll_sticky_clear", 3:"ept_reset", 4:"si5344_62p5mhz_config", 5:"si5344_50mhz_config"}
        button_grid = QtWidgets.QGridLayout()

        self.cb = QtWidgets.QComboBox()
        self.cb.addItem("Full 65MHz setup")
        self.cb.addItem("CDR Reset")
        self.cb.addItem("PLL Sticky Clear")
        self.cb.addItem("Reset Timing Endpoint")
        self.cb.addItem("65MHz Chip Setup")
        self.cb.addItem("50MHz Chip Setup")
        button_grid.addWidget(self.cb, 0, 0)

        write_button = QtWidgets.QPushButton('Send')
        write_button.setToolTip("Run a script that's on the WIB")
        write_button.clicked.connect(lambda: self.send_script())

        button_grid.addWidget(write_button, 1, 0)
        
        self.setLayout(button_grid)
        
    def send_script(self):
        index = self.cb.currentIndex()
        req = wibpb.Script()
        rep = wibpb.Status()
        script_file = self.script_dict[index]
        req.script = bytes(script_file, 'utf-8')
        req.file = True
        self.parent.print_gui(f"Sending {script_file}")
        if not self.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success:{rep.success}")
        
class WIBButtons8(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.script = WIBScript(self)
        layout.addWidget(self.script)
