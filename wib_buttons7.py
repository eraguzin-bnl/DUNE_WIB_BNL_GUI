#!/usr/bin/env python3

import os
import sys
import time
import pickle
import argparse
import numpy as np
from collections import deque
from functools import partial

from wib import WIB
import wib_pb2 as wibpb

try:
    from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui
except:
    from matplotlib.backends.backend_qt4agg import QtCore, QtWidgets, QtGui
    
#Looking at how it's done here:
#https://github.com/DUNE-DAQ/dune-wib-firmware/blob/04440d52f629d8c3e5948fe29616b5b98ff90748/sw/src/femb_3asic.cc#L210
#https://github.com/DUNE-DAQ/dune-wib-firmware/blob/04440d52f629d8c3e5948fe29616b5b98ff90748/sw/src/wib_3asic.cc#L348
class ChannelControlButtons(QtWidgets.QGroupBox):
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
        cb.setToolTip("Set the gain of the LArASIC channel")
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
        cb.addItem("900 mV")
        cb.addItem("200 mV")
        cb.setCurrentIndex(1)
        cb.setToolTip("Set the baseline of the LArASIC channel")
        return cb

    def monitor(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("Off")
        cb.addItem("On")
        cb.setToolTip("Set whether to connect this channel to the monitor output")
        return cb

    def buffer(self):
        cb = QtWidgets.QComboBox()
        cb.addItem("Off")
        cb.addItem("Single On")
        cb.setToolTip("Turn this channe's single ended buffer on or off\nNote: Is overridden if the global differential buffer is on")
        return cb
        
    def __init__(self,parent, femb, asic):
        super().__init__("Channel Control",parent)
        self.parent = parent
        button_grid = QtWidgets.QGridLayout()
        self.channels = 16
        self.femb = femb
        self.asic = asic
        #Remap these settings to the actual chip settings
        self.gain_dict = {0:3, 1:1, 2:0, 3:2}
        self.pulse_dict = {0:2, 1:0, 2:3, 3:1}
        self.monitor_dict = {0:0, 1:1, 2:3}
        self.ch_settings = {
                "Test Cap": self.testcap,
                "Gain": self.gain,
                "Peaking Time": self.peaking_time,
                "Baseline": self.baseline,
                "Monitor": self.monitor,
                "Buffer": self.buffer
                }

        for i,(k,v) in enumerate(self.ch_settings.items()):
            label = QtWidgets.QLabel(k)
            button_grid.addWidget(label, 0, 1+i)
            
        for i in range(self.channels):
            ch_button = QtWidgets.QPushButton(f"Ch {i}")
            ch_button.setToolTip(f"Write channel {i} settings")
            ch_button.clicked.connect(partial(self.sendChannel, i))
            button_grid.addWidget(ch_button, 1+i, 0)
            for j,(k,v) in enumerate(self.ch_settings.items()):
                widget = v()
                widget.setObjectName(f"{k}{self.femb}{self.asic}{i}")
                print(f"{k}{self.femb}{self.asic}{i}")
                widget.setParent(self.parent)
                button_grid.addWidget(widget, 1+i, 1+j)
        self.setLayout(button_grid)

        offset = self.channels + 1
        settings_label = QtWidgets.QLabel("Global LArASIC Settings")
        settings_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(settings_label, offset+1, 1, 1, 6)

        #Global settings row 1
        coupling_label = QtWidgets.QLabel("Coupling")
        coupling_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(coupling_label, offset+2, 1)

        self.coupling_cb = QtWidgets.QComboBox()
        self.coupling_cb.addItem("AC")
        self.coupling_cb.addItem("DC")
        self.coupling_cb.setToolTip("Set the global coupling for the LArASIC chip")
        button_grid.addWidget(self.coupling_cb, offset+3, 1)

        buffer_label = QtWidgets.QLabel("Buffer")
        buffer_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(buffer_label, offset+2, 2)

        self.buffer_cb = QtWidgets.QComboBox()
        self.buffer_cb.addItem("Off")
        self.buffer_cb.addItem("Differential On")
        self.buffer_cb.setToolTip("Turn the global LArASIC differential buffer on or off\n(will override the individual channel buffer setting)")
        button_grid.addWidget(self.buffer_cb, offset+3, 2)

        leakage_label = QtWidgets.QLabel("Leakage\nCurrent")
        leakage_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(leakage_label, offset+2, 3)

        self.leakage_cb = QtWidgets.QComboBox()
        self.leakage_cb.addItem("100 pA")
        self.leakage_cb.addItem("500 pA")
        self.leakage_cb.addItem("1 nA")
        self.leakage_cb.addItem("5 nA")
        self.leakage_cb.setToolTip("Set the global leakage current for the LArASIC chip")
        button_grid.addWidget(self.leakage_cb, offset+3, 3)

        monitor_label = QtWidgets.QLabel("Ch0\nMonitor")
        monitor_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(monitor_label, offset+2, 4)

        self.monitor_cb = QtWidgets.QComboBox()
        self.monitor_cb.addItem("Analog")
        self.monitor_cb.addItem("Temperature")
        self.monitor_cb.addItem("Bandgap")
        self.monitor_cb.setToolTip("Set the monitor output of Channel 0\n(The default is analog)")
        button_grid.addWidget(self.monitor_cb, offset+3, 4)

        filter_label = QtWidgets.QLabel("Ch15\nFilter")
        filter_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(filter_label, offset+2, 5)

        self.filter_cb = QtWidgets.QComboBox()
        self.filter_cb.addItem("Off")
        self.filter_cb.addItem("On")
        self.filter_cb.setToolTip("Connect ASIC CH15 to the high frequency filter")
        button_grid.addWidget(self.filter_cb, offset+3, 5)

        #Global settings row 2
        pulser_dac_label = QtWidgets.QLabel("DAC Gain\nMatching")
        pulser_dac_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(pulser_dac_label, offset+4, 1)

        self.match_cb = QtWidgets.QComboBox()
        self.match_cb.addItem("On")
        self.match_cb.addItem("Off")
        self.match_cb.setToolTip("Allows gain to change. Turning off locks it at 4.7 mV/fC\nDefault is 'on', read datasheet for more details")
        button_grid.addWidget(self.match_cb, offset+5, 1)

        pulser_label = QtWidgets.QLabel("Pulser\nDAC Setting")
        pulser_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(pulser_label, offset+4, 2)

        self.pulser_cb = QtWidgets.QComboBox()
        self.pulser_cb.addItem("Disconnected")
        self.pulser_cb.addItem("Internal")
        self.pulser_cb.addItem("External")
        self.pulser_cb.addItem("Measure")
        self.pulser_cb.setToolTip("Set the configuration of DAC pulser switches\nThe LArASIC P5A does not have an external option anymore\nDo NOT enable switches while the analog monitors are enabled!")
        button_grid.addWidget(self.pulser_cb, offset+5, 2)

        pulser_dac_label = QtWidgets.QLabel("Pulser\nDAC Value")
        pulser_dac_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(pulser_dac_label, offset+4, 3)

        self.dac_sb = QtWidgets.QSpinBox()
        self.dac_sb.setRange(0, 0x3F)
        self.dac_sb.setDisplayIntegerBase(16)
        font = self.dac_sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        self.dac_sb.setFont(font)
        self.dac_sb.setToolTip("Internal DAC value for LArASIC test pulses")
        button_grid.addWidget(self.dac_sb, offset+5, 3)
            
        send_button = QtWidgets.QPushButton('Send global settings only')
        send_button.setToolTip('Send these values to the WIB')
        send_button.clicked.connect(lambda: self.sendGlobal())
        button_grid.addWidget(send_button, offset+6, 1, 1, 4)

        all_button = QtWidgets.QPushButton('Send all channels and global settings')
        all_button.setToolTip('Send these values to the WIB')
        all_button.clicked.connect(lambda: self.sendAll())
        button_grid.addWidget(all_button, offset+7, 1, 1, 4)
        
        test_button = QtWidgets.QPushButton('Pulser')
        test_button.setToolTip('Turn the pulser on and off')
        test_button.clicked.connect(lambda: self.pulse())
        button_grid.addWidget(test_button, offset+8, 1, 1, 4)
        
        self.pulse_status = False
        
    def pulse(self):
        command_bytes = bytearray(f"cd-i2c {0} {1} {2} {0} {20} {1}\n", 'utf-8')
        #command_bytes.extend(f"cd-i2c {1} {1} {2} {0} {20} {1}\n".encode())
        #command_bytes.extend(f"cd-i2c {2} {1} {2} {0} {20} {1}\n".encode())
        #command_bytes.extend(f"cd-i2c {3} {1} {2} {0} {20} {1}\n".encode())
        #command_bytes.extend(b"fast edge_act")
        req = wibpb.Script()
        req.script = bytes(command_bytes)
        rep = wibpb.Status()
        if not self.parent.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success:{rep.success}")

    def getChannelVal(self, ch):
        test_cap_box = self.parent.findChild(QtWidgets.QComboBox, f"Test Cap{self.femb}{self.asic}{ch}")
        test_cap = 1 if (test_cap_box.currentIndex() == 0) else 0
        baseline_box = self.parent.findChild(QtWidgets.QComboBox, f"Baseline{self.femb}{self.asic}{ch}")
        baseline = baseline_box.currentIndex()
        monitor_box = self.parent.findChild(QtWidgets.QComboBox, f"Monitor{self.femb}{self.asic}{ch}")
        monitor = monitor_box.currentIndex()
        buffer_box = self.parent.findChild(QtWidgets.QComboBox, f"Buffer{self.femb}{self.asic}{ch}")
        buffer_val = buffer_box.currentIndex()
        gain_box = self.parent.findChild(QtWidgets.QComboBox, f"Gain{self.femb}{self.asic}{ch}")
        gain = self.gain_dict[gain_box.currentIndex()]
        peak_box = self.parent.findChild(QtWidgets.QComboBox, f"Peaking Time{self.femb}{self.asic}{ch}")
        peak_time = self.pulse_dict[peak_box.currentIndex()]

        channel_val = (test_cap << 0) + (baseline << 1) + (gain << 2) + (peak_time << 4) + (monitor << 6) + (buffer_val << 7)
        return (channel_val)

    def sendChannel(self, ch):
        coldata = self.asic // 4
        chip_num = (self.asic % 4)+1
        command = f"cd-i2c {self.femb} {coldata} {2} {chip_num} {80 + ch} {self.getChannelVal(ch):00X}\n"
        command_bytes = bytes(command, 'utf-8')
        return_string = command_bytes.decode('utf-8')
        self.parent.print_gui(f"Sending command\n{return_string}")

        req = wibpb.Script()
        req.script = command_bytes
        rep = wibpb.Status()
        if not self.parent.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success:{rep.success}")
            
        #https://github.com/DUNE-DAQ/dune-wib-firmware/blob/master/sw/src/femb_3asic.cc#L214
        command = f"cd-i2c {self.femb} {coldata} {2} {0} {20} {8}\n"
        command_bytes = bytearray(command, 'utf-8')
        #command_bytes.extend(b"fast edge_act")
        return_string = command_bytes.decode('utf-8')
        self.parent.print_gui(f"Sending command2\n{return_string}")

        req = wibpb.Script()
        req.script = bytes(command_bytes)
        rep = wibpb.Status()
        if not self.parent.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success2:{rep.success}")
            
        req = wibpb.CDFastCmd()
        req.cmd = 2
        rep = wibpb.Empty()
        self.parent.parent.wib.send_command(req,rep)
        self.parent.print_gui(f"Fast command 'act' sent")

    def getGlobalVal(self):
        match_val = self.match_cb.currentIndex()
        buffer_val = self.buffer_cb.currentIndex()
        coupling_val = 1 if (self.coupling_cb.currentIndex() == 0) else 0
        leak_box_val = self.leakage_cb.currentIndex()
        leak = (leak_box_val%2 == 0)
        leak_10x = (leak_box_val//2 == 1)
        filter_val = self.filter_cb.currentIndex()
        monitor_val = self.monitor_dict[self.monitor_cb.currentIndex()]
        dac_switch = self.pulser_cb.currentIndex()
        dac_val = int(self.dac_sb.value())

        global_reg1 = (match_val << 0) + (buffer_val << 1) + (coupling_val << 2) + (leak_10x << 3) + (filter_val << 4) + (monitor_val << 5) + (leak << 7)

        global_reg2 = (dac_val << 0) + (dac_switch << 6)

        return(global_reg1, global_reg2)

    def sendGlobal(self):
        glo1, glo2 = self.getGlobalVal()
        coldata = self.asic // 4
        chip_num = (self.asic % 4) + 1
        command_bytes = bytearray(f"cd-i2c {self.femb} {coldata} {2} {chip_num} {90} {glo1:00X}\n", 'utf-8')
        command_bytes.extend(f"cd-i2c {self.femb} {coldata} {2} {chip_num} {91} {glo2:00X}\n".encode())
        command_bytes.extend(f"cd-i2c {self.femb} {coldata} {2} {chip_num} {90} {glo1:00X}\n".encode())
        command_bytes.extend(f"cd-i2c {self.femb} {coldata} {2} {chip_num} {91} {glo2:00X}\n".encode())
        return_string = command_bytes.decode('utf-8')
        self.parent.print_gui(f"Sending command\n{return_string}")

        req = wibpb.Script()
        req.script = bytes(command_bytes)
        rep = wibpb.Status()
        if not self.parent.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success:{rep.success}")
            
        command_bytes = bytearray(f"cd-i2c {self.femb} {coldata} {2} {0} {20} {8}\n", 'utf-8')
        #command_bytes.extend(b"fast edge_act")
        return_string = command_bytes.decode('utf-8')
        self.parent.print_gui(f"Sending command3\n{return_string}")

        req = wibpb.Script()
        req.script = bytes(command_bytes)
        rep = wibpb.Status()
        if not self.parent.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success3:{rep.success}")
            
        req = wibpb.CDFastCmd()
        req.cmd = 2
        rep = wibpb.Empty()
        self.parent.parent.wib.send_command(req,rep)
        self.parent.print_gui(f"Fast command 'act' sent")

    def sendAll(self):
        glo1, glo2 = self.getGlobalVal()
        coldata = self.asic // 4
        chip_num = self.asic % 4
        command_bytes = bytearray(f"cd-i2c {self.femb} {0} {2} {chip_num} {0x90} {glo1}\n", 'utf-8')
        command_bytes.extend(f"cd-i2c {self.femb} {0} {2} {chip_num} {0x91} {glo2}\n".encode())
        command_bytes.extend(f"cd-i2c {self.femb} {1} {2} {chip_num} {0x90} {glo1}\n".encode())
        command_bytes.extend(f"cd-i2c {self.femb} {1} {2} {chip_num} {0x91} {glo2}\n".encode())

        for i in range(self.channels):
            command_bytes.extend(f"cd-i2c {self.femb} {coldata} {2} {chip_num} {0x80 + i} {self.getChannelVal(i)}\n".encode())

        return_string = command_bytes.decode('utf-8')
        self.parent.print_gui(f"Sending command\n{return_string}")

        req = wibpb.Script()
        req.script = bytes(command_bytes)
        rep = wibpb.Status()
        if not self.parent.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"Success:{rep.success}")

class ChannelPane(QtWidgets.QMainWindow):
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        self.print_gui = self.parent.print_gui
        _main = QtWidgets.QWidget()
        _main.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setCentralWidget(_main)
        layout = QtWidgets.QVBoxLayout(_main)

        self.FEMBs = 4
        self.ASICs = 8
        wib_function_layout = QtWidgets.QHBoxLayout()
        femb_tabs = QtWidgets.QTabWidget()
        for i in range(self.FEMBs):
            asic_tabs = QtWidgets.QTabWidget()
            for j in range(self.ASICs):
                asic = ChannelControlButtons(self, i, j)
                asic_widget = QtWidgets.QWidget()
                asic_widget.layout = QtWidgets.QVBoxLayout(asic_widget)
                asic_widget.layout.addWidget(asic)
                asic_tabs.addTab(asic_widget,f"ASIC{j}")

            femb_widget = QtWidgets.QWidget()
            femb_widget.layout = QtWidgets.QVBoxLayout(femb_widget)
            femb_widget.layout.addWidget(asic_tabs)
            femb_tabs.addTab(femb_widget,f"FEMB{i}")

        wib_function_layout.addWidget(femb_tabs)
        layout.addLayout(wib_function_layout)
        
class WIBButtons7(QtWidgets.QMainWindow):
    def __init__(self, wib, print_function):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function

        #This method with _main, ChContent and ChLayout allows there to be a horizontal scroll bar
        self._main = QtWidgets.QScrollArea()
        self._main.setWidget(QtWidgets.QWidget())
        self.setCentralWidget(self._main)
        layout = QtWidgets.QVBoxLayout(self._main)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)

        ChContent = QtWidgets.QWidget(self._main)

        ChLayout = QtWidgets.QVBoxLayout(ChContent)
        ChContent.setLayout(ChLayout)
        ChLayout.addWidget(ChannelPane(self))
        self._main.setWidget(ChContent)
