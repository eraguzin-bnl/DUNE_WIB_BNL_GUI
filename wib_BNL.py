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
        #wib_ip_input.setInputMask("000.000.000.000")
        wib_comm_layout.addWidget(self.wib_ip_input)
        self.wib_ip_input.editingFinished.connect(self.wib_address_edited)
        self.wib_ip_input.setToolTip('Insert WIB IP Address')
        
        button = QtWidgets.QPushButton('Confirm new WIB address')
        wib_comm_layout.addWidget(button)
        button.setToolTip('Save plot layout and selected signals')
        button.clicked.connect(self.check_wib)
        layout.addLayout(wib_comm_layout)
        ###
        
        self.grid = QtWidgets.QGridLayout()
        self.views = []
        layout.addLayout(self.grid)
        
        nav_layout = QtWidgets.QHBoxLayout()
        
        button = QtWidgets.QPushButton('Configure Window')
        nav_layout.addWidget(button)
        button.setToolTip('Configure WIB and front end')
        #button.clicked.connect(self.configure_wib)
        
        button = QtWidgets.QPushButton('Plot Window')
        nav_layout.addWidget(button)
        button.setToolTip('Read WIB Spy Buffer')
        #button.clicked.connect(self.acquire_data)
        
        self.text_box = QtWidgets.QGroupBox("text_box")
        self.output_rd = QtWidgets.QTextBrowser(self.text_box)
        self.output_rd.setGeometry(QtCore.QRect(10, 90, 331, 111))
        self.output_rd.setObjectName("text_here")
        nav_layout.addWidget(self.output_rd)

        layout.addLayout(nav_layout)
        
        self.output_rd.append(self.getsometext())
        
    def getsometext(self):
        return "test text"
    
    def check_wib(self):
        self.output_rd.append("ok")
        
    def wib_address_edited(self):
        ip_text_field = self.wib_ip_input.text()
        try:
            ip = ipaddress.ip_address(ip_text_field)
            self.output_rd.append("IP Address changed to {}".format(ip))
        except:
            self.output_rd.append("Not a valid IP address")

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