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
from wib_buttons2 import WIBButtons2
from wib_buttons3 import WIBButtons3
from wib_buttons4 import WIBButtons4
from wib_buttons5 import WIBButtons5
from wib_buttons6 import WIBButtons6
from wib_buttons7 import WIBButtons7

from wib import WIB
import wib_pb2 as wibpb

try:
    from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui
except:
    from matplotlib.backends.backend_qt4agg import QtCore, QtWidgets, QtGui

class WIBMain(QtWidgets.QMainWindow):
    def __init__(self,config_path):
        super().__init__()        
        text_box = QtWidgets.QGroupBox("text_box")
        self.text = QtWidgets.QTextBrowser(text_box)
        self.showMaximized()
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
        
        restart_button = QtWidgets.QPushButton('Restart Communication')
        wib_comm_layout.addWidget(restart_button)
        restart_button.setToolTip('Restart ZeroMQ interface (usually needed after a timeout)')
        restart_button.clicked.connect(self.restart_zmq)
        
        save_config_button = QtWidgets.QPushButton('Save Configuration')
        wib_comm_layout.addWidget(save_config_button)
        save_config_button.setToolTip('Save current layout configuration')
        
        load_config_button = QtWidgets.QPushButton('Load Configuration')
        wib_comm_layout.addWidget(load_config_button)
        load_config_button.setToolTip('Load previous layout configuration')
        
        save_log_button = QtWidgets.QPushButton('Save Log')
        wib_comm_layout.addWidget(save_log_button)
        save_log_button.setToolTip('Save text log output to disk')
        save_log_button.clicked.connect(self.save_log)
        
        layout.addLayout(wib_comm_layout)
        ###
        #The bottom part of the vertical is a horizontal row of 3 elements:
        #Data display, control, and text feedback. They're all separated by a splitter so they can be resized
        #So it goes from layout -> HBox -> splitter -> individual widgets, which have tab widgets
        #If a tabbed widget will be scrollable, that happens inside that widget's class
        
        wib_function_layout = QtWidgets.QHBoxLayout()
        horiz_splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        left_tabs = QtWidgets.QTabWidget()
        
        power_tab = QtWidgets.QWidget()
        power_tab.layout = QtWidgets.QVBoxLayout(power_tab)
        wib_mon = WIBMon(self.wib, self.gui_print)
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
        
        wib_buttons_tab = QtWidgets.QWidget()
        wib_buttons_tab.layout = QtWidgets.QVBoxLayout(wib_buttons_tab)
        buttons1 = WIBButtons1(self.wib, self.gui_print)
        wib_buttons_tab.layout.addWidget(buttons1)
        self.wib_modules.append(buttons1)
        buttons2 = WIBButtons2(self.wib, self.gui_print)
        wib_buttons_tab.layout.addWidget(buttons2)
        self.wib_modules.append(buttons2)
        buttons3 = WIBButtons3(self.wib, self.gui_print)
        wib_buttons_tab.layout.addWidget(buttons3)
        self.wib_modules.append(buttons3)
        buttons6 = WIBButtons6(self.wib, self.gui_print)
        wib_buttons_tab.layout.addWidget(buttons6)
        self.wib_modules.append(buttons6)
        right_tabs.addTab(wib_buttons_tab,"WIB Control")
        
        femb_buttons_tab = QtWidgets.QWidget()
        femb_buttons_tab.layout = QtWidgets.QVBoxLayout(femb_buttons_tab)
        buttons4 = WIBButtons4(self.wib, self.gui_print)
        femb_buttons_tab.layout.addWidget(buttons4)
        self.wib_modules.append(buttons4)
        right_tabs.addTab(femb_buttons_tab,"FEMB Control")

        channel_buttons_tab = QtWidgets.QWidget()
        channel_buttons_tab.layout = QtWidgets.QVBoxLayout(channel_buttons_tab)
        buttons7 = WIBButtons7(self.wib, self.gui_print)
        channel_buttons_tab.layout.addWidget(buttons7)
        self.wib_modules.append(buttons7)
        right_tabs.addTab(channel_buttons_tab,"Channel Control")

        power_buttons_tab = QtWidgets.QWidget()
        power_buttons_tab.layout = QtWidgets.QVBoxLayout(power_buttons_tab)
        buttons5 = WIBButtons5(self.wib, self.gui_print)
        power_buttons_tab.layout.addWidget(buttons5)
        self.wib_modules.append(buttons5)
        right_tabs.addTab(power_buttons_tab,"Power Config")
        
        horiz_splitter.addWidget(left_tabs)
        horiz_splitter.addWidget(right_tabs)
        horiz_splitter.addWidget(self.text)
#        horiz_splitter.setStretchFactor(1, 1)
#        horiz_splitter.setSizes([150, 150, 50])
        
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
        self.text.append(f"IP Address changed to {ip_text_field}")
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
        
    def save_log(self):
        name = QtWidgets.QFileDialog.getSaveFileName(None, "Save Text Log", "", "*.txt")
        file = open(name[0],'w')
        text = self.text.toPlainText()
        file.write(text)
        file.close()
        
    def restart_zmq(self):
        ip_text_field = self.wib_ip_input.text()
        del self.wib
        self.wib = WIB(ip_text_field)
        self.text.append(f"ZeroMQ interface restarted with IP Address of {ip_text_field}")
        for i in self.wib_modules:
            i.wib = self.wib

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
            self.parent_reference.gui_print(f"Error: Cannot change IP Address to {ip_string}")
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
