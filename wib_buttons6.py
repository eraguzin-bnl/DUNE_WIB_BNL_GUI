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
    
class WIBFast(QtWidgets.QGroupBox):
    def __init__(self,parent):
        super().__init__("Fast Command")
        self.parent = parent
        #fast_cmds = { 'reset':1, 'act':2, 'sync':4, 'edge':8, 'idle':16, 'edge_act':32 }
        self.command_dict = {0:1, 1:2, 2:4, 3:8, 4:16, 5:32}
        button_grid = QtWidgets.QGridLayout()

        self.cb = QtWidgets.QComboBox()
        self.cb.addItem("Reset")
        self.cb.addItem("Act")
        self.cb.addItem("Sync")
        self.cb.addItem("Edge")
        self.cb.addItem("Idle")
        self.cb.addItem("Edge_Act")
        button_grid.addWidget(self.cb, 0, 0)

        write_button = QtWidgets.QPushButton('Send')
        write_button.setToolTip('Send the fast command to all FEMBs')
        write_button.clicked.connect(lambda: self.femb_conf_write())

        button_grid.addWidget(write_button, 1, 0)
        
        self.setLayout(button_grid)
        
    def fast_command(self):
        index = self.cb.currentIndex()
        req = wibpb.CDFastCmd()
        req.cmd = self.command_dict[index]
        rep = wibpb.Empty()
        wib.send_command(req,rep)
        print('Fast command sent')
        
class WIBButtons6(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        layout.addWidget(WIBFast(self))
