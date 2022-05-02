#!/usr/bin/env python3

from json import load
import os
import sys
import time
import pickle
import argparse
import numpy as np
from collections import deque

from wib import WIB
import wib_pb2 as wibpb
import json

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
        cb.addItem("900 mV")
        cb.addItem("200 mV")
        cb.setCurrentIndex(1)
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
        cb.addItem("Differential On")
        cb.setToolTip("Turn the LArASIC differential buffer on or off")
        return cb
        
    def strobe_skip(self):
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 0xFFFFFFF)
        sb.setDisplayIntegerBase(16)
        sb.setValue(255)
        font = sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        sb.setFont(font)
        sb.setToolTip("Test pulse - 2MHz periods to skip after strobe")
        return sb
        
    def strobe_delay(self):
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 0xFFFFFFF)
        sb.setDisplayIntegerBase(16)
        sb.setValue(255)
        font = sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        sb.setFont(font)
        sb.setToolTip("Test pulse - offset from 2MHz to start strobe in 64MHz periods")
        return sb
        
    def strobe_length(self):
        sb = QtWidgets.QSpinBox()
        sb.setRange(0, 0xFFFFFFF)
        sb.setDisplayIntegerBase(16)
        sb.setValue(255)
        font = sb.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        sb.setFont(font)
        sb.setToolTip("Test pulse - length of strobe in 64MHz periods")
        return sb
        
    def __init__(self,parent):
        super().__init__("FEMB Control",parent)
        self.parent = parent
        button_grid = QtWidgets.QGridLayout()
        self.fembs = 4
        self.first_run = True
        #Remap these settings to the actual chip settings
        #https://github.com/DUNE-DAQ/dune-wib-firmware/blob/master/sw/src/femb_3asic.cc#L191
        #Don't know why gain dict breaks the rules
        self.gain_dict = {0:2, 1:1, 2:3, 3:0}
        self.pulse_dict = {0:1, 1:0, 2:3, 3:2}
        self.femb_settings = {
                "Enable": self.enabled,
                "Test Cap": self.testcap,
                "Gain": self.gain,
                "Peaking Time": self.peaking_time,
                "Baseline": self.baseline,
                "Pulse DAC": self.dac,
                "Leakage Current": self.leakage,
                "Coupling": self.coupling,
                "Differential Buffer": self.buffer,
                "Strobe Skip": self.strobe_skip,
                "Strobe Delay": self.strobe_delay,
                "Strobe Length": self.strobe_length
                }
        for i,(k,v) in enumerate(self.femb_settings.items()):
            label = QtWidgets.QLabel(k)
            button_grid.addWidget(label, 1+i, 0)
            
        for i in range(self.fembs):
            label = QtWidgets.QLabel(f"FEMB {i}")
            button_grid.addWidget(label, 0, 1+i)
            for j,(k,v) in enumerate(self.femb_settings.items()):
                widget = v()
                widget.setObjectName(f"{k}{i}")
                widget.setParent(self.parent)
                button_grid.addWidget(widget, 1+j, 1+i)
        self.setLayout(button_grid)
        
        #Global settings row 1
        offset = len(self.femb_settings)
        pulser_label = QtWidgets.QLabel("COLDATA Pulser")
        pulser_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(pulser_label, offset+1, 1)
        
        self.pulser_box = QtWidgets.QComboBox()
        self.pulser_box.addItem("On")
        self.pulser_box.addItem("Off")
        self.pulser_box.setToolTip("Initiate the COLDATA to pulse to the FEMBs")
        button_grid.addWidget(self.pulser_box, offset+2, 1)
        
        temp_label = QtWidgets.QLabel("Temp Settings")
        temp_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(temp_label, offset+1, 2)
        
        self.temp_box = QtWidgets.QComboBox()
        self.temp_box.addItem("Warm")
        self.temp_box.addItem("Cold")
        self.temp_box.setToolTip("Indicate whether the COLDATA and COLDADC should use warm or cold default settings")
        button_grid.addWidget(self.temp_box, offset+2, 2)
        
        adc_test_label = QtWidgets.QLabel("ADC Test")
        adc_test_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(adc_test_label, offset+1, 3)
        
        self.adc_test_box = QtWidgets.QComboBox()
        self.adc_test_box.addItem("Off")
        self.adc_test_box.addItem("On")
        self.adc_test_box.setToolTip("Enable ADC Test Pattern?")
        button_grid.addWidget(self.adc_test_box, offset+2, 3)
        
        frame_label = QtWidgets.QLabel("Frame")
        frame_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(frame_label, offset+1, 4)
        
        self.frame_box = QtWidgets.QComboBox()
        self.frame_box.addItem("FRAME-14")
        self.frame_box.addItem("FRAME-DD")
        self.frame_box.setToolTip("COLDATA Data format (default is FRAME-14)")
        button_grid.addWidget(self.frame_box, offset+2, 4)
        
        #Global settings row 2
        offset = offset + 3
        adc_reg_label = QtWidgets.QLabel("COLDADC\nRegister\nOverride")
        adc_reg_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        button_grid.addWidget(adc_reg_label, offset, 0)
        self.adc_check = QtWidgets.QCheckBox()
        button_grid.addWidget(self.adc_check, offset+1, 0)
        for num,i in enumerate([0,4,24,25,26,27,29,30]):
            adc_reg = QtWidgets.QLabel(f"Reg{i}")
            adc_reg.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
            button_grid.addWidget(adc_reg, offset+(2*(num//4)), 1+num%4)
            
            sb = QtWidgets.QSpinBox()
            sb.setRange(0, 0xFF)
            sb.setDisplayIntegerBase(16)
            font = sb.font()
            font.setCapitalization(QtGui.QFont.AllUppercase)
            sb.setFont(font)
            sb.setToolTip(f"Override COLDADC Reg {i}")
            sb.setObjectName(f"reg{i}")
            sb.setParent(self.parent)
            button_grid.addWidget(sb, offset+(2*(num//4))+1, 1+num%4)
            
        send_button = QtWidgets.QPushButton('Send')
        send_button.setToolTip('Send these values to the WIB')
        send_button.clicked.connect(lambda: self.sendFEMB())
        button_grid.addWidget(send_button, offset+4, 1)
        
        self.ch_box = QtWidgets.QSpinBox()
        self.ch_box.setRange(0, 0xFF)
        self.ch_box.setDisplayIntegerBase(16)
        self.ch_box.setValue(0x81)
        font = self.ch_box.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        self.ch_box.setFont(font)
        self.ch_box.setToolTip("Sets all channels to this")
        
        self.glo1_box = QtWidgets.QSpinBox()
        self.glo1_box.setRange(0, 0xFF)
        self.glo1_box.setDisplayIntegerBase(16)
        self.glo1_box.setValue(0x0)
        font = self.glo1_box.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        self.glo1_box.setFont(font)
        self.glo1_box.setToolTip("Sets all Global 1 regs to this")
        
        self.glo2_box = QtWidgets.QSpinBox()
        self.glo2_box.setRange(0, 0xFF)
        self.glo2_box.setDisplayIntegerBase(16)
        self.glo2_box.setValue(0x09)
        font = self.glo2_box.font()
        font.setCapitalization(QtGui.QFont.AllUppercase)
        self.glo2_box.setFont(font)
        self.glo2_box.setToolTip("Sets all Global 2 regs to this")
        
        button_grid.addWidget(self.ch_box, offset+5, 1)
        button_grid.addWidget(self.glo1_box, offset+5, 2)
        button_grid.addWidget(self.glo2_box, offset+5, 3)
        
        send_button = QtWidgets.QPushButton('Send2')
        send_button.setToolTip('Write to all ASIC channel and globals')
        send_button.clicked.connect(lambda: self.sendFEMB2())
        button_grid.addWidget(send_button, offset+6, 1)


        load_button = QtWidgets.QPushButton('Load Config')
        load_button.setToolTip('Load configuration values from JSON file')
        load_button.clicked.connect(lambda: self.load())
        button_grid.addWidget(load_button, offset+4, 3)

        save_button = QtWidgets.QPushButton('Save Config')
        save_button.setToolTip('Save configuration values to JSON file')
        save_button.clicked.connect(lambda: self.save())
        button_grid.addWidget(save_button, offset+4, 4)
        self.settings_cb = {"Test Cap":"test_cap", "Gain":"gain" , "Peaking Time": "peak_time", "Baseline": "baseline",
             "Leakage Current": "leak", "Coupling": "ac_couple", "Differential Buffer": "buffer"}
        self.settings_sb = {"Pulse DAC": "pulse_dac", "Strobe Skip": "strobe_skip", "Strobe Delay": "strobe_delay", "Strobe Length": "strobe_length" }


    def save(self):
        self.saveDict = { "cold": bool(self.temp_box.currentIndex()),
                          "pulser": False if self.pulser_box.currentIndex() == 1 else True,
                          "enabled_fembs": [bool(self.parent.findChild(QtWidgets.QComboBox, f"Enable{i}").currentIndex()) for i in range(4)],
                          "femb_configs": [ { "test_cap": False if self.parent.findChild(QtWidgets.QComboBox, "Test Cap0").currentIndex() == 1 else True,
                                              "gain": self.parent.findChild(QtWidgets.QComboBox, "Gain0").currentIndex(),
                                              "peak_time": self.parent.findChild(QtWidgets.QComboBox, "Peaking Time0").currentIndex(),
                                              "baseline": self.parent.findChild(QtWidgets.QComboBox, "Baseline0").currentIndex(),
                                              "pulse_dac": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC0").value())),
                                              "leak": self.parent.findChild(QtWidgets.QComboBox, "Leakage Current0").currentIndex(),
                                              "leak_10x": False,
                                              "ac_couple": False if self.parent.findChild(QtWidgets.QComboBox, "Coupling0").currentIndex() == 1 else True,
                                              "buffer": self.parent.findChild(QtWidgets.QComboBox, "Differential Buffer0").currentIndex(),
                                              "strobe_skip": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip0").value())),
                                              "strobe_delay": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay0").value())),
                                              "strobe_length": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Length0").value()))
                                            },
                                            { "test_cap": False if self.parent.findChild(QtWidgets.QComboBox, "Test Cap1").currentIndex() == 1 else True,
                                              "gain": self.parent.findChild(QtWidgets.QComboBox, "Gain1").currentIndex(),
                                              "peak_time": self.parent.findChild(QtWidgets.QComboBox, "Peaking Time1").currentIndex(),
                                              "baseline": self.parent.findChild(QtWidgets.QComboBox, "Baseline1").currentIndex(),
                                              "pulse_dac": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC1").value())),
                                              "leak": self.parent.findChild(QtWidgets.QComboBox, "Leakage Current1").currentIndex(),
                                              "leak_10x": False,
                                              "ac_couple": False if self.parent.findChild(QtWidgets.QComboBox, "Coupling1").currentIndex() == 1 else True,
                                              "buffer": self.parent.findChild(QtWidgets.QComboBox, "Differential Buffer1").currentIndex(),
                                              "strobe_skip": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip1").value())),
                                              "strobe_delay": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay1").value())),
                                              "strobe_length": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Length1").value()))
                                            },
                                            { "test_cap": False if self.parent.findChild(QtWidgets.QComboBox, "Test Cap2").currentIndex() == 1 else True,
                                              "gain": self.parent.findChild(QtWidgets.QComboBox, "Gain2").currentIndex(),
                                              "peak_time": self.parent.findChild(QtWidgets.QComboBox, "Peaking Time2").currentIndex(),
                                              "baseline": self.parent.findChild(QtWidgets.QComboBox, "Baseline2").currentIndex(),
                                              "pulse_dac": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC2").value())),
                                              "leak": self.parent.findChild(QtWidgets.QComboBox, "Leakage Current2").currentIndex(),
                                              "leak_10x": False,
                                              "ac_couple": False if self.parent.findChild(QtWidgets.QComboBox, "Coupling2").currentIndex() == 1 else True,
                                              "buffer": self.parent.findChild(QtWidgets.QComboBox, "Differential Buffer2").currentIndex(),
                                              "strobe_skip": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip2").value())),
                                              "strobe_delay": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay2").value())),
                                              "strobe_length": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Length2").value()))
                                            },
                                            { "test_cap": False if self.parent.findChild(QtWidgets.QComboBox, "Test Cap3").currentIndex() == 1 else True,
                                              "gain": self.parent.findChild(QtWidgets.QComboBox, "Gain3").currentIndex(),
                                              "peak_time": self.parent.findChild(QtWidgets.QComboBox, "Peaking Time3").currentIndex(),
                                              "baseline": self.parent.findChild(QtWidgets.QComboBox, "Baseline3").currentIndex(),
                                              "pulse_dac": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC3").value())),
                                              "leak": self.parent.findChild(QtWidgets.QComboBox, "Leakage Current3").currentIndex(),
                                              "leak_10x": False,
                                              "ac_couple": False if self.parent.findChild(QtWidgets.QComboBox, "Coupling3").currentIndex() == 1 else True,
                                              "buffer": self.parent.findChild(QtWidgets.QComboBox, "Differential Buffer3").currentIndex(),
                                              "strobe_skip": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip3").value())),
                                              "strobe_delay": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay3").value())),
                                              "strobe_length": int(str(self.parent.findChild(QtWidgets.QSpinBox, "Strobe Length3").value()))
                                            }

                          ]


        }
        for i in range(4):
            indx = self.parent.findChild(QtWidgets.QComboBox, f"Leakage Current{i}").currentIndex()
            print(indx)
            if (indx == 2 or indx == 3):
                print(i, "yes")
                self.saveDict["femb_configs"][i]["leak_10x"] = True
                self.saveDict["femb_configs"][i]["leak"] = indx - 2
        fileWrite = self.saveFileDialog()
        if (fileWrite != "Cancel"):
            with open(fileWrite, 'w') as file:
                json.dump(self.saveDict, file)

    def load(self):
        fileLoader = self.openFileNameDialog()
        if (fileLoader != "Cancel"):
            with open(fileLoader, 'r') as file:
                self.config = json.load(file)

            self.temp_box.setCurrentIndex(self.config["cold"])
            if (self.config["pulser"] == False):
                self.pulser_box.setCurrentIndex(1)
            else:
                self.pulser_box.setCurrentIndex(0)
            for i in range(4):
                self.parent.findChild(QtWidgets.QComboBox, f"Enable{i}").setCurrentIndex(self.config["enabled_fembs"][i])
            for key,value in self.settings_sb.items():
                for i in range(4):
                    self.parent.findChild(QtWidgets.QSpinBox, f"{key}{i}").setValue(int(hex(self.config["femb_configs"][i][value]), 16))
            for key,value in self.settings_cb.items():
                for i in range(4):
                    if ((key == "Test Cap" or key == "Coupling") and self.config["femb_configs"][i][value] == False):
                        self.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(1)
                    elif ((key == "Test Cap" or key == "Coupling") and self.config["femb_configs"][i][value] == True):
                        self.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(0)
                    elif (key == "Leakage Current"):
                        if (self.config["femb_configs"][i]["leak_10x"] == True):
                            self.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(self.config["femb_configs"][i][value]+2)
                        else:
                            self.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(self.config["femb_configs"][i][value])
                    else:
                        self.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(self.config["femb_configs"][i][value])
            
            
            

    def openFileNameDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","JSON Files (*.json)", options=options)
        if fileName:
            return fileName
        else:
            return "Cancel"

    def saveFileDialog(self):
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog
        fileName, _ = QtWidgets.QFileDialog.getSaveFileName(self,"QFileDialog.getSaveFileName()","","JSON Files (*.json)", options=options)
        if fileName:
            return fileName
        else:
            return "Cancel"
        
        
        
    def sendFEMB2(self):
        for i in range(1, 5, 1):
            for j in range(0x80, 0x90, 1):
                self.coldata_poke(0, 0, 2, i, j, self.ch_box.value())
                self.coldata_poke(0, 0, 3, i, j, self.ch_box.value())
            self.coldata_poke(0, 0, 2, i, 0x90, self.glo1_box.value())
            self.coldata_poke(0, 0, 2, i, 0x91, self.glo2_box.value())
            self.coldata_poke(0, 0, 3, i, 0x90, self.glo1_box.value())
            self.coldata_poke(0, 0, 3, i, 0x91, self.glo2_box.value())
        
        self.coldata_poke(0, 0, 2, 0, 0x20, 8)
        self.coldata_poke(0, 0, 3, 0, 0x20, 8)
        
        req = wibpb.CDFastCmd()
        req.cmd = 2
        rep = wibpb.Empty()
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui(f"Fast command sent")
        
        self.coldata_poke(0, 0, 2, 0, 0x20, 3)
        self.coldata_poke(0, 0, 2, 0, 0x20, 3)
        
        req = wibpb.CDFastCmd()
        req.cmd = 2
        rep = wibpb.Empty()
        self.parent.wib.send_command(req,rep)
        self.parent.print_gui(f"Fast command sent")
        
        self.coldata_peek(0, 0, 2, 0, 0x24)
        self.coldata_peek(0, 0, 3, 0, 0x24)
        
        
    def coldata_peek(self, femb, coldata, chip_addr, page, reg):
        req = wibpb.CDPeek()
        rep = wibpb.CDRegValue()
        req.femb_idx = femb
        req.coldata_idx = coldata
        req.chip_addr = chip_addr
        req.reg_page = page
        req.reg_addr = reg
        if not self.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"FEMB 0x{rep.femb_idx:01X}, COLDATA 0x{rep.coldata_idx:01X}")
            self.parent.print_gui(f"Chip Address 0x{rep.chip_addr:02X}, Page 0x{rep.reg_page:02X}")
            self.parent.print_gui(f"Register 0x{rep.reg_addr:02X} was read as 0x{rep.data:02X}")
        
    def coldata_poke(self, femb, coldata, chip_addr, page, reg, data):
        req = wibpb.CDPoke()
        rep = wibpb.CDRegValue()
        req.femb_idx = femb
        req.coldata_idx = coldata
        req.chip_addr = chip_addr
        req.reg_page = page
        req.reg_addr = reg
        req.data = data
        if not self.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.print_gui(f"FEMB 0x{rep.femb_idx:01X}, COLDATA 0x{rep.coldata_idx:01X}")
            self.parent.print_gui(f"Chip Address 0x{rep.chip_addr:02X}, Page 0x{rep.reg_page:02X}")
            self.parent.print_gui(f"Register 0x{rep.reg_addr:02X} was written to 0x{rep.data:02X}")
        
    def sendFEMB(self):
        req = wibpb.ConfigureWIB()
        for i in range(self.fembs):
            femb_conf = req.fembs.add();
            for j,(k,v) in enumerate(self.femb_settings.items()):
                enable_box = self.parent.findChild(QtWidgets.QComboBox, f"Enable{i}")
                femb_conf.enabled = (enable_box.currentIndex() == 1)
                test_cap_box = self.parent.findChild(QtWidgets.QComboBox, f"Test Cap{i}")
                femb_conf.test_cap = (test_cap_box.currentIndex() == 0)
                gain_box = self.parent.findChild(QtWidgets.QComboBox, f"Gain{i}")
                femb_conf.gain = self.gain_dict[gain_box.currentIndex()]
                peak_box = self.parent.findChild(QtWidgets.QComboBox, f"Peaking Time{i}")
                femb_conf.peak_time = self.pulse_dict[peak_box.currentIndex()]
                baseline_box = self.parent.findChild(QtWidgets.QComboBox, f"Baseline{i}")
                femb_conf.baseline = baseline_box.currentIndex()
                dac_box = self.parent.findChild(QtWidgets.QSpinBox, f"Pulse DAC{i}")
                femb_conf.pulse_dac = int(dac_box.value())
                
                leak_box_val = self.parent.findChild(QtWidgets.QComboBox, f"Leakage Current{i}").currentIndex()
                femb_conf.leak = (leak_box_val%2 == 0)
                femb_conf.leak_10x = (leak_box_val//2 == 1)
                
                couple_box = self.parent.findChild(QtWidgets.QComboBox, f"Coupling{i}")
                femb_conf.ac_couple = (couple_box.currentIndex() == 0)
                buffer_box = self.parent.findChild(QtWidgets.QComboBox, f"Differential Buffer{i}")
                femb_conf.buffer = 2*(buffer_box.currentIndex())
                skip_box = self.parent.findChild(QtWidgets.QSpinBox, f"Strobe Skip{i}")
                femb_conf.strobe_skip = int(skip_box.value())
                delay_box = self.parent.findChild(QtWidgets.QSpinBox, f"Strobe Delay{i}")
                femb_conf.strobe_delay = int(delay_box.value())
                length_box = self.parent.findChild(QtWidgets.QSpinBox, f"Strobe Length{i}")
                femb_conf.strobe_length = int(length_box.value())
                
        req.cold = (self.temp_box.currentIndex() == 1)
        req.pulser = (self.pulser_box.currentIndex() == 0)
        req.adc_test_pattern = (self.adc_test_box.currentIndex() == 1)
        req.frame_dd = (self.frame_box.currentIndex() == 1)
        
        if (self.adc_check.isChecked()):
            req.adc_conf.reg_0 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg0").value())
            req.adc_conf.reg_4 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg4").value())
            req.adc_conf.reg_24 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg24").value())
            req.adc_conf.reg_25 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg25").value())
            req.adc_conf.reg_26 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg26").value())
            req.adc_conf.reg_27 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg27").value())
            req.adc_conf.reg_29 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg29").value())
            req.adc_conf.reg_30 = int(self.parent.findChild(QtWidgets.QSpinBox, "reg30").value())
        self.parent.print_gui('Sending ConfigureWIB command')
        rep = wibpb.Status()
        if not self.parent.wib.send_command(req,rep,self.parent.print_gui):
            self.parent.change_pulser_status(req.pulser)
            self.parent.print_gui(f"Success:{rep.success}")
        
class WIBButtons4(QtWidgets.QWidget):
    def __init__(self, wib, print_function, pulser_status):
        QtWidgets.QWidget.__init__(self)
        self.wib = wib
        self.print_gui = print_function
        self.change_pulser_status = pulser_status
        layout = QtWidgets.QVBoxLayout(self)
        layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        self.fembcontrol = FEMBControlButtons(self)
        layout.addWidget(self.fembcontrol)
