#!/usr/bin/env python3

import os
import sys
import ipaddress
import time
import pickle
import argparse
import numpy as np
import configparser
import datetime
from collections import deque
from wib_scope import WIBScope
from wib_mon import WIBMon
from femb_diagnostic import FEMBDiagnostics
from wib_buttons1 import WIBButtons1

from wib import WIB
import wib_pb2 as wibpb

try:
    from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui
except:
    from matplotlib.backends.backend_qt4agg import QtCore, QtWidgets, QtGui

class WIBMain(QtWidgets.QMainWindow):
    def __init__(self,config_path):
        super().__init__()        
        
        self.parse_config(config_path)
        self.wib = WIB(self.wib_address)
        self.wib_modules = []
        #Main Widget that encompasses everything, everything flows vertically from here
        _main = QtWidgets.QWidget()
        _main.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setCentralWidget(_main)
        layout = QtWidgets.QVBoxLayout(_main)
        ###
        #Top widget is setting the WIB IP address and options for saving and recalling configuration
        wib_comm_layout = QtWidgets.QHBoxLayout()
        
        #Will only allow valid IP addresses, or else error will prompt user in text box
        #TODO add functionality to these buttons
        self.wib_ip_input = QtWidgets.QLineEdit(self.wib_address)
        wib_comm_layout.addWidget(self.wib_ip_input)
        self.wib_ip_input.setValidator(ValidIP(self))
        self.wib_ip_input.editingFinished.connect(self.wib_address_edited)
        self.wib_ip_input.setToolTip("Insert WIB IP Address and push 'enter'")
        
        save_button = QtWidgets.QPushButton('Save Configuration')
        wib_comm_layout.addWidget(save_button)
        save_button.setToolTip('Save current layout configuration')
        
        load_button = QtWidgets.QPushButton('Load Configuration')
        wib_comm_layout.addWidget(load_button)
        load_button.setToolTip('Load previous layout configuration')
        
        layout.addLayout(wib_comm_layout)
        ###
        #The bottom part of the vertical is a horizontal row of 3 elements:
        #Data display, control, and text feedback. They're all separated by a splitter so they can be resized
        #So it goes from layout -> HBox -> splitter -> individual widgets, which have tab widgets
        #If a tabbed widget will be scrollable, that happens inside that widget's class
        text_box = QtWidgets.QGroupBox("text_box")
        self.text = QtWidgets.QTextBrowser(text_box)
        
        wib_function_layout = QtWidgets.QHBoxLayout()
        horiz_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        left_tabs = QtWidgets.QTabWidget()
        
        power_tab = QtWidgets.QWidget()
        power_tab.layout = QtWidgets.QVBoxLayout(power_tab)
        wib_mon = WIBMon(self.wib)
        self.wib_modules.append(wib_mon)
        power_tab.layout.addWidget(wib_mon)
        left_tabs.addTab(power_tab,"Power Monitoring")
        scope_tab = QtWidgets.QWidget()
        scope_tab.layout = QtWidgets.QVBoxLayout(scope_tab)
        wib_scope = WIBScope(self.wib)
        self.wib_modules.append(wib_scope)
        scope_tab.layout.addWidget(wib_scope)
        left_tabs.addTab(scope_tab,"WIB Oscilloscope")
        femb_tab = QtWidgets.QWidget()
        femb_tab.layout = QtWidgets.QVBoxLayout(femb_tab)
        femb_diagnostics = FEMBDiagnostics(self.wib)
        self.wib_modules.append(femb_diagnostics)
        femb_tab.layout.addWidget(femb_diagnostics)
        left_tabs.addTab(femb_tab,"FEMB Diagnostics")
        
        right_tabs = QtWidgets.QTabWidget()
        
        buttons1_tab = QtWidgets.QWidget()
        buttons1_tab.layout = QtWidgets.QVBoxLayout(buttons1_tab)
        buttons1_tab.layout.addWidget((WIBButtons1(self.wib, self.gui_print)))
        right_tabs.addTab(buttons1_tab,"WIB Control")
        
        horiz_splitter.addWidget(left_tabs)
        horiz_splitter.addWidget(right_tabs)
        horiz_splitter.addWidget(self.text)
        horiz_splitter.setStretchFactor(1, 1)
        horiz_splitter.setSizes([150, 150, 50])
        
        wib_function_layout.addWidget(horiz_splitter)
        layout.addLayout(wib_function_layout)
        self.text.append("Welcome to the BNL WIB Interface!\n"
                              "Please start by making sure the WIB is powered and connected "
                              "to this terminal and press 'Power On/Connect'")
        
#Run once the text field validates the IP Address. If new, will need to flush old WIB() object from memory 
#since ZeroMQ socket objects are already created with old IP address.
    def wib_address_edited(self):
        ip_text_field = self.wib_ip_input.text()
        del self.wib
        self.wib = WIB(ip_text_field)
        self.text.append("IP Address changed to {}".format(ip_text_field))
        for i in self.wib_modules:
            i.wib = self.wib
        
#Checks to get all relevant parameters from external config file that users can change
    def parse_config(self, config_path):
        try:
            config.read(config_path, encoding='utf-8')
            self.wib_address = config["DEFAULT"]["WIB_ADDRESS"]
            self.default_femb = config["DEFAULT"]["FEMB"]
        except:
            self.gui_print("Error: Config file not found at {}. Using default values")
            self.wib_address = "192.168.121.1"
            self.default_femb = 0
            
    def gui_print(self, text):
        self.text.append("---------------")
        self.text.append(str(datetime.datetime.now()))
        self.text.append(text)

#PyQT needs a separate class to be the validator
class ValidIP(QtGui.QValidator):
    def __init__(self, parent):
        QtGui.QValidator.__init__(self, parent)
        self.parent_reference = parent
        
#Rather than use complicated Regex, just use a simple Python library to check if valid IP, also cleans it up
    def validate(self, ip_string, pos):
        try:
            ip = ipaddress.ip_address(ip_string)
            return (QtGui.QValidator.Acceptable, format(ip), pos)
        except:
            self.parent_reference.gui_print("Error: Cannot change IP Address to {}".format(ip_string))
            return (QtGui.QValidator.Invalid, ip_string, pos)
        
if __name__ == "__main__":
    config = configparser.ConfigParser()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(current_dir, "settings.ini")

    #Prevent kernel dying in second run
    #https://stackoverflow.com/questions/40094086/python-kernel-dies-for-second-run-of-pyqt5-gui
    qapp = QtCore.QCoreApplication.instance()
    if qapp is None:
        qapp = QtWidgets.QApplication(sys.argv)
        
    qapp.setApplicationName("DUNE WIB - BNL Interface")
    app = WIBMain(config_path)
    try:
        app.setWindowIcon(QtGui.QIcon('img/dune.png'))
    except:
        pass
    
    app.show()
    qapp.exec_()
