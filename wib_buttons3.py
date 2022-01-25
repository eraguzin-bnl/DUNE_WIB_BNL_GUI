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
    
#This was absurdly annoying. QSpinBox can do hexidecimal input fields with:
#self.reg_box.setDisplayIntegerBase(16)
#However, QSpinBox only goes up to 2^31 bits. People have done their own kluges:
#https://stackoverflow.com/questions/26581444/qspinbox-with-unsigned-int-for-hex-input
#But here's mine. I wanted to use a QDoubleSpinBox for the additional range, but it doesn't have
#setDisplayIntegerBase. To organize it and overwrite the proper functions, I made it its own class
    
#So first I needed to set a validator that makes sure the input is hex. With just a validator, there's no hex.
#You scroll up and it just does decimal numbers. You try to put in a hex value and it treats it as 0
#So that's why I needed to overwrite valueFromText. It takes the input and writes it as the internal spinbox
#value as if it were a hex. Without that, I found that pressing up and down on the arrows would ignore the
#hex values that you typed. Then when the value is validated, I need textFromValue to print it in hex format
    
class MySpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, parent=None):
        super(MySpinBox, self).__init__(parent)
        # any RegExp that matches the allowed input
        self.validator = QtGui.QRegExpValidator(QtCore.QRegExp("[x0-9A-Fa-f]{1,8}"), self)
        #self.setPrefix("0x")
        
    def validate(self, text, pos):
        return self.validator.validate(text, pos)
    
    def textFromValue(self, double):
        return format(int(double), 'x')
    
    def valueFromText(self, double):
        return int(double, 16)
    
class WIBRegControlButtons(QtWidgets.QGroupBox):
    def __init__(self,parent, name, bits):
        super().__init__(f"{name} Registers ({bits} bit)",parent)
        self.parent = parent
        button_grid = QtWidgets.QGridLayout()
        
        lbl_0x1 = QtWidgets.QLabel("0x")
        lbl_0x1.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        lbl_0x2 = QtWidgets.QLabel("0x")
        lbl_0x2.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        
        reg_label = QtWidgets.QLabel("Register")
        reg_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        
        value_label = QtWidgets.QLabel("Value")
        value_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        
        reading_label = QtWidgets.QLabel("Result")
        reading_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        
        self.reg_box = MySpinBox()
        self.reg_box.setRange(0, (2**bits)-1)
#        self.reg_box.setValue(0)
#        self.reg_box.setDisplayIntegerBase(16)
        font = self.reg_box.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        self.reg_box.setFont(font)
        self.reg_box.setToolTip(f"{name} Register ({bits} bits, hex)")
        
        self.val_box = MySpinBox()
        self.val_box.setRange(0, (2**bits)-1)
#        self.val_box.setValue(0)
#        self.val_box.setDisplayIntegerBase(16)
        self.val_box.setFont(font)
        self.val_box.setToolTip("{name} Register Value({bits} bits, hex)")
        
        self.result = QtWidgets.QLabel()
        self.result.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        
        button_grid.addWidget(lbl_0x1, 5, 1)
        button_grid.addWidget(reg_label, 4, 2)
        button_grid.addWidget(lbl_0x2, 5, 3)
        button_grid.addWidget(value_label, 4, 4)
        
        button_grid.addWidget(self.reg_box, 5, 2)
        button_grid.addWidget(self.val_box, 5, 4)
        
        read_button = QtWidgets.QPushButton('Read')
        read_button.setToolTip('Read the value of this register')
        
        write_button = QtWidgets.QPushButton('Write')
        write_button.setToolTip('Write the value of this register')
        
        if (name == "WIB"):
            read_button.clicked.connect(lambda: self.wib_peek(self.reg_box.value()))
            write_button.clicked.connect(lambda: self.wib_poke(self.reg_box.value(), self.val_box.value()))
            
        else:
            femb_label = QtWidgets.QLabel("FEMB(0-3)")
            femb_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            button_grid.addWidget(femb_label, 0, 2)
            
            self.femb_box = QtWidgets.QSpinBox()
            self.femb_box.setRange(0, 3)
            self.femb_box.setFont(font)
            self.femb_box.setToolTip("Which FEMB on the WIB?")
            button_grid.addWidget(self.femb_box, 1, 2)
            
            femb_label = QtWidgets.QLabel("COLDATA(0-1)")
            femb_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            button_grid.addWidget(femb_label, 0, 4)
            
            self.coldata_box = QtWidgets.QSpinBox()
            self.coldata_box.setRange(0, 1)
            self.coldata_box.setFont(font)
            self.coldata_box.setToolTip("Which COLDATA on the FEMB?")
            button_grid.addWidget(self.coldata_box, 1, 4)
            
            page_label = QtWidgets.QLabel("Page")
            page_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            button_grid.addWidget(page_label, 0, 6)
            
            lbl_0xpage = QtWidgets.QLabel("0x")
            lbl_0xpage.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
            button_grid.addWidget(lbl_0xpage, 1, 5)
            
            self.page_box = QtWidgets.QSpinBox()
            self.page_box.setRange(0, 0xF)
            self.page_box.setDisplayIntegerBase(16)
            self.page_box.setFont(font)
            self.page_box.setToolTip("8 bit page in COLDATA")
            button_grid.addWidget(self.page_box, 1, 6)
            
            read_button.clicked.connect(lambda: self.coldata_peek(self.femb_box.value(),
                                                                  self.coldata_box.value(),
                                                                  self.page_box.value(),
                                                                  self.reg_box.value()))
            write_button.clicked.connect(lambda: self.coldata_poke(self.femb_box.value(),
                                                                  self.coldata_box.value(),
                                                                  self.page_box.value(),
                                                                  self.reg_box.value(),
                                                                  self.val_box.value()))
        
        button_grid.addWidget(read_button, 6, 2)
        button_grid.addWidget(write_button, 6, 4)
        button_grid.addWidget(reading_label, 5, 5)
        button_grid.addWidget(self.result, 6, 5)
        
        self.setLayout(button_grid)
        
    def wib_peek(self, reg):
        req = wibpb.Peek()
        rep = wibpb.RegValue()
        req.addr = reg
        self.parent.wib.send_command(req,rep)
        self.result.setText(f"{rep.value:08x}")
        self.parent.print_gui(f"Register 0x{rep.addr:016X} was read as 0x{rep.value:08X}")
        
    def wib_poke(self, reg, val):
        req = wibpb.Poke()
        rep = wibpb.RegValue()
        req.addr = reg
        req.value = val
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui(f"Register 0x{rep.addr:016X} was set to 0x{rep.value:08X}")
        
    def coldata_peek(self, femb, coldata, page, reg):
        req = wibpb.CDPeek()
        rep = wibpb.CDRegValue()
        req.femb_idx = femb
        req.coldata_idx = coldata
        req.reg_page = page
        req.reg_addr = reg
        self.parent.wib.send_command(req,rep)
        self.result.setText(f"{rep.data:02x}")
        self.parent.print_gui(f"FEMB 0x{rep.femb_idx:01X}, COLDATA 0x{rep.coldata_idx:01X}")
        self.parent.print_gui(f"Chip Address 0x{rep.chip_addr:02X}, Page 0x{rep.reg_page:02X}")
        self.parent.print_gui(f"Register 0x{rep.reg_addr:02X} was read as 0x{rep.data:02X}")
        
    def coldata_poke(self, femb, coldata, page, reg, data):
        req = wibpb.CDPoke()
        rep = wibpb.CDRegValue()
        req.femb_idx = femb
        req.coldata_idx = coldata
        req.reg_page = page
        req.reg_addr = reg
        req.data = data
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui(f"FEMB 0x{rep.femb_idx:01X}, COLDATA 0x{rep.coldata_idx:01X}")
        self.parent.print_gui(f"Chip Address 0x{rep.chip_addr:02X}, Page 0x{rep.reg_page:02X}")
        self.parent.print_gui(f"Register 0x{rep.reg_addr:02X} was written to 0x{rep.data:02X}")
        
class WIBButtons3(QtWidgets.QWidget):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        layout.addWidget(WIBRegControlButtons(self, "WIB", 32))
        layout.addWidget(WIBRegControlButtons(self, "COLDATA", 8))