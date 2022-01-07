#!/usr/bin/env python3

import os
import sys
import ipaddress
import time
import pickle
import argparse
import numpy as np
import configparser
from collections import deque
from wib_scope import WIBScope
from wib_mon import WIBMon

from wib import WIB
#import wib_pb2 as wibpb

try:
    from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui
except:
    from matplotlib.backends.backend_qt4agg import QtCore, QtWidgets, QtGui

class WIBMain(QtWidgets.QMainWindow):
    def __init__(self,wib_server,config='default.json'):
        super().__init__()        
        self.wib = WIB(wib_server)
        self.config = config
        
        self._main = QtWidgets.QWidget()
        self._main.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)
        
        ###
        wib_comm_layout = QtWidgets.QHBoxLayout()
        
        self.wib_ip_input = QtWidgets.QLineEdit(wib_server)
        wib_comm_layout.addWidget(self.wib_ip_input)
        self.wib_ip_input.setValidator(ValidIP(self))
        self.wib_ip_input.editingFinished.connect(self.wib_address_edited)
        self.wib_ip_input.setToolTip("Insert WIB IP Address and push 'enter'")
        
        save_button = QtWidgets.QPushButton('Save Configuration')
        wib_comm_layout.addWidget(save_button)
        save_button.setToolTip('Save current layout configuration')
        #button.clicked.connect(self.configure_wib)
        
        load_button = QtWidgets.QPushButton('Load Configuration')
        wib_comm_layout.addWidget(load_button)
        load_button.setToolTip('Load previous layout configuration')
        #button.clicked.connect(self.configure_wib)
        
        layout.addLayout(wib_comm_layout)
        ###
        
        nav_layout = QtWidgets.QHBoxLayout()
        
        # Initialize tab screen
        self.tabs = QtWidgets.QTabWidget()
        self.tab1 = QtWidgets.QWidget()
        self.tab2 = QtWidgets.QWidget()
        #self.tabs.resize(300,200)
        
        # Add tabs
        self.tabs.addTab(self.tab1,"Tab 1")
        self.tabs.addTab(self.tab2,"Tab 2")
        
        # Create first tab
        self.tab1.layout = QtWidgets.QVBoxLayout(self)
        self.tab1.layout.addWidget((WIBScope()))
        self.tab1.setLayout(self.tab1.layout)
        
        #Create second tab
        self.tab2.layout = QtWidgets.QVBoxLayout(self)
        self.tab2.layout.addWidget((WIBMon()))
        self.tab2.setLayout(self.tab2.layout)
        
        # Add tabs to widget
        nav_layout.addWidget(self.tabs, 40)
        
        
        # Initialize tab screen
        self.tabs2 = QtWidgets.QTabWidget()
        self.tab3 = QtWidgets.QWidget()
        #self.tabs2.resize(300,200)
        
        # Add tabs
        self.tabs2.addTab(self.tab3,"Tab 3")
        
        # Create first tab
        self.tab3.layout = QtWidgets.QVBoxLayout(self)
        self.tab3.layout.addWidget((WIBScope()))
        self.tab3.setLayout(self.tab3.layout)
        
        nav_layout.addWidget(self.tabs2, 40)
        
        
        self.text_box = QtWidgets.QGroupBox("text_box")
        self.output_rd = QtWidgets.QTextBrowser(self.text_box)
        self.output_rd.setGeometry(QtCore.QRect(10, 90, 331, 111))
        self.output_rd.setObjectName("text_here")
        nav_layout.addWidget(self.output_rd, 20)

        layout.addLayout(nav_layout)
        #self.setLayout(nav_layout)
        self.output_rd.append("test text")
        
        print(self.tabs.sizeHint())
        print(self.tabs2.sizeHint())
        print(self.output_rd.sizeHint())
        print(self.tabs.sizePolicy())
        print(self.tabs2.sizePolicy())
        print(self.output_rd.sizePolicy())
        
    def wib_address_edited(self):
        ip_text_field = self.wib_ip_input.text()
        del self.wib
        self.wib = WIB(ip_text_field)
        self.output_rd.append("IP Address changed to {}".format(ip_text_field))

class ValidIP(QtGui.QValidator):
    def __init__(self, parent):
        QtGui.QValidator.__init__(self, parent)
        self.parent_reference = parent

    def validate(self, ip_string, pos):
        try:
            ip = ipaddress.ip_address(ip_string)
            return (QtGui.QValidator.Acceptable, format(ip), pos)
        except:
            self.parent_reference.output_rd.append("Error: Cannot change IP Address to {}".format(ip_string))
            return (QtGui.QValidator.Invalid, ip_string, pos)
        
if __name__ == "__main__":
    config = configparser.ConfigParser()
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "settings.ini")

    try:
        config.read(file_path, encoding='utf-8')
        wib_address = config["DEFAULT"]["WIB_ADDRESS"]
    except:
        wib_address = "192.168.121.1"

    #Prevent kernel dying in second run
    #https://stackoverflow.com/questions/40094086/python-kernel-dies-for-second-run-of-pyqt5-gui
    qapp = QtCore.QCoreApplication.instance()
    if qapp is None:
        qapp = QtWidgets.QApplication(sys.argv)
        
    qapp.setApplicationName("DUNE WIB - BNL Interface")
    app = WIBMain(wib_address)
    app.setWindowIcon(QtGui.QIcon('img/dune.png'))
    app.show()
    qapp.exec_()