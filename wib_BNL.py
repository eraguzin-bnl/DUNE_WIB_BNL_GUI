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
from wib_buttons7 import ChannelControlButtons, WIBButtons7
from wib_buttons8 import WIBButtons8

from wib import WIB
import wib_pb2 as wibpb
import json

try:
    from matplotlib.backends.qt_compat import QtCore, QtWidgets, QtGui
except:
    from matplotlib.backends.backend_qt4agg import QtCore, QtWidgets, QtGui

class WIBMain(QtWidgets.QMainWindow):
    
    def __init__(self,config_path):
        super().__init__()        
        text_box = QtWidgets.QGroupBox("text_box")
        self.text = QtWidgets.QTextBrowser(text_box)
        #self.showMaximized()
        self.parse_config(config_path)
        self.wib = WIB(self.wib_address)
        self.wib_modules = []
        #If the pulser is on or not, so multiple areas of GUI can make decisions based on that
        self.pulser = False
        #Global setting for if certain FEMBs are initiated, so that the acquire_data() method knows which buffers to request
        self.buf0_status = False
        self.buf1_status = False
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
        
        pulser_button = QtWidgets.QPushButton('Toggle Pulser')
        wib_comm_layout.addWidget(pulser_button)
        pulser_button.setToolTip('Toggle pulser between "on" and "off". See indicator for current status')
        pulser_button.clicked.connect(self.toggle_pulser)
        
        pulser_label = QtWidgets.QLabel('Pulser Status')
        wib_comm_layout.addWidget(pulser_label)
        
        self.pulser_status = QtWidgets.QLabel("Off")
        self.pulser_status.setMinimumWidth(30)
        wib_comm_layout.addWidget(self.pulser_status)
        self.pulser_status.setToolTip('Current status of the pulser. Can be changed by writing to FEMB or individual chips')
        
        restart_button = QtWidgets.QPushButton('Restart Communication')
        wib_comm_layout.addWidget(restart_button)
        restart_button.setToolTip('Restart ZeroMQ interface (usually needed after a timeout)')
        restart_button.clicked.connect(self.restart_zmq)
        
        save_config_button = QtWidgets.QPushButton('Save Configuration')
        wib_comm_layout.addWidget(save_config_button)
        save_config_button.setToolTip('Save current layout configuration')
        save_config_button.clicked.connect(self.write)
        
        load_config_button = QtWidgets.QPushButton('Load Configuration')
        wib_comm_layout.addWidget(load_config_button)
        load_config_button.setToolTip('Load previous layout configuration')
        load_config_button.clicked.connect(self.read)
        
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
        wib_scope = WIBScope(self.wib, self.gui_print, self.get_femb_on)
        self.wib_modules.append(wib_scope)
        scope_tab.layout.addWidget(wib_scope)
        left_tabs.addTab(scope_tab,"WIB Oscilloscope")
        femb_tab = QtWidgets.QWidget()
        femb_tab.layout = QtWidgets.QVBoxLayout(femb_tab)
        femb_diagnostics = FEMBDiagnostics(self.wib, self.gui_print, self.get_femb_on)
        self.wib_modules.append(femb_diagnostics)
        femb_tab.layout.addWidget(femb_diagnostics)
        left_tabs.addTab(femb_tab,"FEMB Diagnostics")
        
        right_tabs = QtWidgets.QTabWidget()
        
        wib_buttons_tab = QtWidgets.QWidget()
        wib_buttons_tab.layout = QtWidgets.QVBoxLayout(wib_buttons_tab)

        self.buttons1 = WIBButtons1(self.wib, self.gui_print, self.set_femb_on)
        wib_buttons_tab.layout.addWidget(self.buttons1)
        self.wib_modules.append(self.buttons1)
        self.buttons2 = WIBButtons2(self.wib, self.gui_print)
        wib_buttons_tab.layout.addWidget(self.buttons2)
        self.wib_modules.append(self.buttons2)
        self.buttons3 = WIBButtons3(self.wib, self.gui_print)
        wib_buttons_tab.layout.addWidget(self.buttons3)
        self.wib_modules.append(self.buttons3)
        
        double_widget = QtWidgets.QWidget()
        double_widget.layout = QtWidgets.QHBoxLayout(double_widget)
        self.buttons6 = WIBButtons6(self.wib, self.gui_print)
        double_widget.layout.addWidget(self.buttons6)
        
        self.buttons8 = WIBButtons8(self.wib, self.gui_print)
        double_widget.layout.addWidget(self.buttons8)
        double_widget.layout.setAlignment(QtCore.Qt.AlignCenter)  #align center
        
        wib_buttons_tab.layout.addWidget(double_widget)
        self.wib_modules.append(self.buttons6)

        _main.scroll_area = QtWidgets.QScrollArea()
        _main.scroll_area.setWidget(wib_buttons_tab)
        
        
        right_tabs.addTab(wib_buttons_tab,"WIB Control")
        
        femb_buttons_tab = QtWidgets.QWidget()
        femb_buttons_tab.layout = QtWidgets.QVBoxLayout(femb_buttons_tab)
        
        self.buttons4 = WIBButtons4(self.wib, self.gui_print, self.set_pulser_status)
        femb_buttons_tab.layout.addWidget(self.buttons4)
        self.wib_modules.append(self.buttons4)
      
        right_tabs.addTab(femb_buttons_tab,"FEMB Control")

        channel_buttons_tab = QtWidgets.QWidget()
        channel_buttons_tab.layout = QtWidgets.QVBoxLayout(channel_buttons_tab)
        self.buttons7 = WIBButtons7(self.wib, self.gui_print, self.toggle_pulser, self.get_pulser_status)
        channel_buttons_tab.layout.addWidget(self.buttons7)
        self.wib_modules.append(self.buttons7)
      
        right_tabs.addTab(channel_buttons_tab,"Channel Control")

        power_buttons_tab = QtWidgets.QWidget()
        power_buttons_tab.layout = QtWidgets.QVBoxLayout(power_buttons_tab)
        self.buttons5 = WIBButtons5(self.wib, self.gui_print)
        power_buttons_tab.layout.addWidget(self.buttons5)
        self.wib_modules.append(self.buttons5)
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
        #screen = QtWidgets.QDesktopWidget().screenGeometry()
        #self.setGeometry(0, 0, screen.width(), screen.height())
    def write(self):
        self.dataWrite = { "wib-control" : { "power-on-sequence" : { "cold-configuration": self.buttons1.power_gb.power_buttons[4].checkState(),
                                                                "power-sequence": self.buttons1.power_gb.power_sequence_box.currentIndex(),
                                                                "FEMB 0": self.buttons1.power_gb.power_buttons[0].checkState(),
                                                                "FEMB 1": self.buttons1.power_gb.power_buttons[1].checkState(),
                                                                "FEMB 2": self.buttons1.power_gb.power_buttons[2].checkState(),
                                                                "FEMB 3": self.buttons1.power_gb.power_buttons[3].checkState()
                                                              },
                                        "wib-client" :        { "log" : self.buttons2.wib_client_buttons.logBox.currentIndex() },
                                        "wib-registers" :     { "register" : hex(int(self.buttons3.wib_name.reg_box.value())),
                                                                "value" : hex(int(self.buttons3.wib_name.val_box.value()))
                                                              },
                                        "coldata-registers" : { "FEMB" : self.buttons3.coldata_name.femb_box.value(),
                                                                "COLDATA" : self.buttons3.coldata_name.coldata_box.value(),
                                                                "chip-addr" : hex(int(self.buttons3.coldata_name.chip_addr_box.value())),
                                                                "page" : hex(int(self.buttons3.coldata_name.page_box.value())),
                                                                "register" : hex(int(self.buttons3.coldata_name.reg_box.value())),
                                                                "value": hex(int(self.buttons3.coldata_name.val_box.value()))
                                                              },
                                        "fast-command" :      { "command" : self.buttons6.fast.cb.currentIndex() },
                                        "scripts" :           { "setup" : self.buttons8.script.cb.currentIndex() }
                                      },
                            "femb-control": { "enable": { "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Enable0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Enable1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Enable2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Enable3").currentIndex()
                                                        },
                                              "testcap": { "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Test Cap0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Test Cap1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Test Cap2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Test Cap3").currentIndex()
                                                        },
                                              "gain": {   "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Gain0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Gain1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Gain2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Gain3").currentIndex()
                                                        },
                                              "peaking-time": { "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Peaking Time0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Peaking Time1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Peaking Time2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Peaking Time3").currentIndex()
                                                        },
                                               "baseline": { "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Baseline0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Baseline1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Baseline2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Baseline3").currentIndex()
                                                        },
                                               "pulse-DAC": { "FEMB 0": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC0").value())),
                                                          "FEMB 1": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC1").value())),
                                                          "FEMB 2": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC2").value())),
                                                         "FEMB 3": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Pulse DAC3").value()))
                                                        },
                                               "leakage-current": { "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Leakage Current0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Leakage Current1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Leakage Current2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Leakage Current3").currentIndex()
                                                        },
                                                "coupling": { "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Coupling0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Coupling1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Coupling2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Coupling3").currentIndex()
                                                        },
                                                "differential-buffer": { "FEMB 0": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Differential Buffer0").currentIndex(),
                                                          "FEMB 1": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Differential Buffer1").currentIndex(),
                                                          "FEMB 2": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Differential Buffer2").currentIndex(),
                                                          "FEMB 3": self.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, "Differential Buffer3").currentIndex()
                                                        },
                                                "strobe-skip": { "FEMB 0": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip0").value())),
                                                          "FEMB 1": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip1").value())),
                                                          "FEMB 2": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip2").value())),
                                                         "FEMB 3": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Skip3").value()))
                                                        },
                                                "strobe-delay": { "FEMB 0": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay0").value())),
                                                          "FEMB 1": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay1").value())),
                                                          "FEMB 2": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay2").value())),
                                                         "FEMB 3": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Delay3").value()))
                                                        },
                                                "strobe-length": { "FEMB 0": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Length0").value())),
                                                                    "FEMB 1": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Length1").value())),
                                                                    "FEMB 2": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Length2").value())),
                                                                    "FEMB 3": hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "Strobe Length3").value()))
                                                        },
                                                "coldata-pulser":  self.buttons4.fembcontrol.pulser_box.currentIndex() ,
                                                "temp-settings" :  self.buttons4.fembcontrol.temp_box.currentIndex() ,
                                                "ADC-test" :  self.buttons4.fembcontrol.adc_test_box.currentIndex() ,
                                                "frame":  self.buttons4.fembcontrol.frame_box.currentIndex() ,
                                                "COLDADC-register-override" :  self.buttons4.fembcontrol.adc_check.checkState() ,
                                                "reg0":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg0").value())) ,
                                                "reg4":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg4").value())) ,
                                                "reg24":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg24").value())) ,
                                                "reg25":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg25").value())) ,
                                                "reg26":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg26").value())) ,
                                                "reg27":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg27").value())) ,
                                                "reg29":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg29").value())) ,
                                                "reg30":  hex(int(self.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, "reg30").value())) ,
                                            } ,
                            "channel-control": { f"FEMB{i}": { f"ASIC{j}" : { f"ch{k}" if k < 17 else "set-all" if k == 17 else "coupling" if k== 18 else "buffer" if k == 19 else "leakage-current" 
                                                                                        if k==20 else "ch0-monitor" if k==21 else "ch15-filter" if k==22 else "DAC-gain-matching" if k ==23 else "pulser-DAC-setting" if k==24 
                                                                                        else "pulser-DAC-value" if k==25 else ""
                                                                                        : {   "test-cap": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Test Cap{k}{j}{i}").currentIndex(),
                                                                                            "gain": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Gain{k}{j}{i}").currentIndex(),
                                                                                            "peaking-time": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Peaking Time{k}{j}{i}").currentIndex(),
                                                                                            "baseline": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Baseline{k}{j}{i}").currentIndex(),
                                                                                            "monitor": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Monitor{k}{j}{i}").currentIndex(),
                                                                                            "buffer": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Buffer{k}{j}{i}").currentIndex()
                                                                                        } if k < 17 else 
                                                                                        {   "test-cap": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Test Cap{k}{j}{i}").currentIndex(),
                                                                                            "gain": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Gain{k}{j}{i}").currentIndex(),
                                                                                            "peaking-time": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Peaking Time{k}{j}{i}").currentIndex(),
                                                                                            "baseline": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Baseline{k}{j}{i}").currentIndex(),
                                                                                            "monitor": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Monitor{k}{j}{i}").currentIndex(),
                                                                                            "buffer": self.buttons7.channelPane.channelButtons[(i*8)+j].findChild(QtWidgets.QComboBox, f"Buffer{k}{j}{i}").currentIndex()
                                                                                        } if k == 17 else
                                                                                        self.buttons7.channelPane.channelButtons[(i*8)+j].coupling_cb.currentIndex() if k== 18 else
                                                                                        self.buttons7.channelPane.channelButtons[(i*8)+j].buffer_cb.currentIndex() if k == 19 else
                                                                                        self.buttons7.channelPane.channelButtons[(i*8)+j].leakage_cb.currentIndex() if k==20 else 
                                                                                        self.buttons7.channelPane.channelButtons[(i*8)+j].monitor_cb.currentIndex() if k==21 else
                                                                                        self.buttons7.channelPane.channelButtons[(i*8)+j].filter_cb.currentIndex() if k==22 else 
                                                                                        self.buttons7.channelPane.channelButtons[(i*8)+j].match_cb.currentIndex() if k ==23 else 
                                                                                        self.buttons7.channelPane.channelButtons[(i*8)+j].pulser_cb.currentIndex() if k==24 else 
                                                                                        hex(int(self.buttons7.channelPane.channelButtons[(i*8)+j].dac_sb.value())) if k==25 else ""
                                                                                        
                                                            
                                                                                                            
                                                                              for k in range(26) 
                                                                            } 
                                                                for j in range(8) 
                                                            } 
                                                for i in range(4)
                                             },
                            "power-config": { "dc-dc-convertor-1": self.buttons5.powerconf.dc1_box.value(),
                                             "dc-dc-convertor-2": self.buttons5.powerconf.dc2_box.value(),
                                             "dc-dc-convertor-3": self.buttons5.powerconf.dc3_box.value(),
                                             "dc-dc-convertor-4": self.buttons5.powerconf.dc4_box.value(),
                                             "ldo-regulator-1": self.buttons5.powerconf.ldo1_box.value(),
                                             "ldo-regulator-2": self.buttons5.powerconf.ldo2_box.value()
                                            }           

 
                                    

                        }
        
        fileWriter = self.saveFileDialog()
        if (fileWriter != "Cancel"):
            with open(fileWriter, 'w') as file:
                json.dump(self.dataWrite, file)

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

    def read(self):
        fileLoader = self.openFileNameDialog()
        if (fileLoader != "Cancel"):
            with open(fileLoader, 'r') as file:
                self.data = json.load(file)
            for i in range(5):
                powButtons = self.buttons1.power_gb.power_buttons
                if i < 4:
                    powButtons[i].setCheckState(self.data['wib-control']['power-on-sequence'][f'FEMB {i}'])
                powButtons[i].setCheckState(self.data['wib-control']['power-on-sequence']['cold-configuration'])
            self.buttons1.power_gb.power_sequence_box.setCurrentIndex(self.data['wib-control']['power-on-sequence']['power-sequence'])
            self.buttons2.wib_client_buttons.logBox.setCurrentIndex(self.data['wib-control']['wib-client']['log'])

            self.buttons3.wib_name.reg_box.setValue(int(self.data['wib-control']['wib-registers']['register'], 16))
            self.buttons3.wib_name.val_box.setValue(int(self.data['wib-control']['wib-registers']['value'], 16))
            colData = self.buttons3.coldata_name
            coldataDict = {colData.femb_box: "FEMB", colData.coldata_box: "COLDATA", colData.chip_addr_box: "chip-addr", colData.page_box: "page", 
                            colData.reg_box: "register", colData.val_box: "value"}
            for key,value in coldataDict.items():
                if (key != (colData.femb_box or colData.coldata_box)):
                    key.setValue(int(self.data['wib-control']['coldata-registers'][f"{value}"], 16))
                else:
                    key.setValue(self.data['wib-control']['coldata-registers'][f'{value}'])
            self.buttons6.fast.cb.setCurrentIndex(self.data['wib-control']['fast-command']['command'])
            self.buttons8.script.cb.setCurrentIndex(self.data['wib-control']['scripts']['setup'])
            fembDict = {"enable": "Enable", "testcap": "Test Cap", "gain": "Gain", "peaking-time": "Peaking Time", "baseline": "Baseline", "pulse-DAC": "Pulse DAC", 
                        "leakage-current": "Leakage Current", "coupling": "Coupling", "differential-buffer": "Differential Buffer", "strobe-skip": "Strobe Skip", 
                        "strobe-delay": "Strobe Delay", "strobe-length": "Strobe Length"}
            fembControl = self.buttons4.fembcontrol
            for i in range(4):
                for key,value in fembDict.items():
                    if (key != ("pulse-DAC" or "strobe-skip" or "strobe-delay" or "strobe-length")):
                        fembControl.parent.findChild(QtWidgets.QComboBox, f"{value}{i}").setCurrentIndex(self.data['femb-control'][f"{key}"]['FEMB {i}'])
                    else:
                        fembControl.fembcontrol.parent.findChild(QtWidgets.QSpinBox, f"{value}{i}").setValue(int(self.data['femb-control'][f"{key}"]['FEMB {i}'], 16))
            fembControl.temp_box.setCurrentIndex(self.data['femb-control']['temp-settings'])
            fembControl.pulser_box.setCurrentIndex(self.data['femb-control']['coldata-pulser'])
            fembControl.adc_test_box.setCurrentIndex(self.data['femb-control']['ADC-test'])
            fembControl.frame_box.setCurrentIndex(self.data['femb-control']['frame'])
            fembControl.adc_check.setCheckState(self.data['femb-control']['COLDADC-register-override'])
            for i in range(0,4,24,25,26,27,29,30):
                fembControl.parent.findChild(QtWidgets.QSpinBox, f"reg{i}").setValue(int(self.data['femb-control'][f'reg{i}'], 16))
            self.buttons5.powerconf.dc1_box.setValue(self.data['power-config']['dc-dc-convertor-1'])
            self.buttons5.powerconf.dc2_box.setValue(self.data['power-config']['dc-dc-convertor-2'])
            self.buttons5.powerconf.dc3_box.setValue(self.data['power-config']['dc-dc-convertor-3'])
            self.buttons5.powerconf.dc4_box.setValue(self.data['power-config']['dc-dc-convertor-4'])
            self.buttons5.powerconf.ldo1_box.setValue(self.data['power-config']['ldo-regulator-1'])
            self.buttons5.powerconf.ldo2_box.setValue(self.data['power-config']['ldo-regulator-2'])

            settingsDict = {"Test Cap":"test-cap", "Gain":"gain" , "Peaking Time": "peaking-time", "Baseline": "baseline", "Monitor": "monitor", "Buffer": "buffer"}
            for i in range(4):
                for j in range(8):
                    channelControl = self.buttons7.channelPane.channelButtons[(i*8)+j]
                    channelControl.coupling_cb.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['coupling'])
                    channelControl.buffer_cb.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['buffer'])
                    channelControl.leakage_cb.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['leakage-current'])
                    channelControl.monitor_cb.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['ch0-monitor'])
                    channelControl.filter_cb.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['ch15-filter'])
                    channelControl.match_cb.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['DAC-gain-matching'])
                    channelControl.pulser_cb.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['pulser-DAC-setting'])
                    channelControl.dac_sb.setValue(int(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"]['pulser-DAC-value'], 16))
                    for k in range(17):
                        for key,value in settingsDict.items():
                            child = channelControl.findChild(QtWidgets.QComboBox, f"{key}{k}{j}{i}")
                            try:
                                child.setCurrentIndex(self.data['channel-control'][f"FEMB{i}"][f"ASIC{j}"][f"ch{k}"][f"{value}"])
                            except:
                                print(f"{key}{k}{j}{i}")

        

        
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
        if (isinstance(name, str)):
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
            
    def toggle_pulser(self):
        command_bytes = bytearray("delay 5\n", 'utf-8')
        #command_bytes.extend(f"cd-i2c {0} {1} {2} {0} {20} {1}\n".encode())
        for i in range(4):
            for j in range(2, 4, 1):
                command_bytes.extend(f"cd-i2c {i} {0} {j} {0} {20} {1}\n".encode())
        
        req = wibpb.Script()
        req.script = bytes(command_bytes)
        return_string = bytes(command_bytes).decode('utf-8')
        #self.gui_print(f"Sending command\n{return_string}")
        rep = wibpb.Status()
        if not self.wib.send_command(req,rep,self.gui_print):
            req = wibpb.CDFastCmd()
            req.cmd = 2
            rep = wibpb.Empty()
            self.wib.send_command(req,rep)
            self.change_pulser_status()
            self.gui_print(f"Pulser toggled")
        else:
            self.gui_print(f"Toggle write:{rep.success}")
            
    def change_pulser_status(self):
        if self.pulser:
            self.pulser = False
            self.pulser_status.setText("Off")
        else:
            self.pulser = True
            self.pulser_status.setText("On")
            
    def set_pulser_status(self, status):
        self.pulser = status
        if status:
            self.pulser_status.setText("On")
        else:
            self.pulser_status.setText("Off")
            
    def get_pulser_status(self):
        return self.pulser
    
    #Once buffers are on, there's no way that they'll return 0 samples, even if you turn the FEMB off after
    #So there's no need to set them false again
    def set_femb_on(self, femb):
        if (femb//2):
            self.buf1_status = True
        else:
            self.buf0_status = True
            
    def get_femb_on(self):
        return self.buf0_status, self.buf1_status

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
    try:
        with open(sys.argv[1]) as json_data:
            datas = json.load(json_data)
            app.buttons4.fembcontrol.temp_box.setCurrentIndex(datas["cold"])
            if (datas["pulser"] == False):
                app.buttons4.fembcontrol.pulser_box.setCurrentIndex(1)
            else:
                app.buttons4.fembcontrol.pulser_box.setCurrentIndex(0)
            for i in range(4):
                app.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, f"Enable{i}").setCurrentIndex(datas["enabled_fembs"][i])
            for key,value in app.buttons4.fembcontrol.settings_sb.items():
                for i in range(4):
                    app.buttons4.fembcontrol.parent.findChild(QtWidgets.QSpinBox, f"{key}{i}").setValue(int(hex(datas["femb_configs"][i][value]), 16))
            for key,value in app.buttons4.fembcontrol.settings_cb.items():
                for i in range(4):
                    if ((key == "Test Cap" or key == "Coupling") and datas["femb_configs"][i][value] == False):
                        app.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(1)
                    elif ((key == "Test Cap" or key == "Coupling") and datas["femb_configs"][i][value] == True):
                        app.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(0)
                    elif (key == "Leakage Current"):
                        if (datas["femb_configs"][i]["leak_10x"] == True):
                            app.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(datas["femb_configs"][i][value]+2)
                        else:
                            app.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(datas["femb_configs"][i][value])
                    else:
                        app.buttons4.fembcontrol.parent.findChild(QtWidgets.QComboBox, f"{key}{i}").setCurrentIndex(datas["femb_configs"][i][value])
            
    except:
       pass
    qapp.exec_()

    
         
