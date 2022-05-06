# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 10:57:07 2019

@author: Edoardo Lopriore
"""
# This is a limited set of control functions for the Keysigt E36312A power supply.
# Options: initialize, turn channels on and off, get channel status, set channel voltage outputs, measure voltages and currents. 

import struct
import sys 
import string
import time
import copy

import pyvisa as visa
#from visa import VisaIOError

class PS_CTL:
    #Initialize power supply Keysight E36312A
    def ps_init(self):
        rm = visa.ResourceManager()
        rm_list = rm.list_resources()
        try:
            rm_list.index(self.ADDR)
            print ("Keysight E36312A power supply (%s) is locacted"%self.ADDR)
        except ValueError:
            print ("Keysight E36312A power supply (%s) is not found, Please check!"%self.ADDR)
            print ("Exit anyway!")
            sys.exit()
        try:
            ps = rm.open_resource(self.ADDR)
        except VisaIOError:
            print ("Keysight E36312A Initialize--> Exact system name not found")
            print ("Exit anyway!")
            sys.exit()
        self.powerSupplyDevice = ps

        #self.powerSupplyDevice.write("*IDN?")
        self.powerSupplyDevice.write("MEAS:VOLT?")
        resp = self.powerSupplyDevice.read().strip()
        print (resp)

#    #Turn on channels
#    def on(self, channels = [1,2,3]):
#        if type(channels) is not list:
#            if ((int(channels) < 1) or (int(channels) > 3)):
#                print("Keysight E36312A Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channels))
#                return
#            self.powerSupplyDevice.write(":OUTP ON,(@{})".format(channels))
#            if (self.get_on_off(channels) != True):
#                print("Keysight E36312A Error --> Tried to turn on Channel {} of the Rigol DP832, but it didn't turn on".format(channels))
#            
#        else:
#            for i in channels:
#                if ((int(i) < 1) or (int(i) > 3)):
#                    print("Keysight E36312A Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(i))
#                    return
#                
#            for i in channels:
#               self.powerSupplyDevice.write(":OUTP ON,(@{})".format(i))
#               if (self.get_on_off(i) != True):
#                   print("Keysight E36312A Error --> Tried to turn on Channel {} of the Rigol DP832, but it didn't turn on".format(i))
#                   
#        return True
#    
#    #Turn off channels
#    def off(self, channels = [1,2,3]):
#        if type(channels) is not list:
#            if ((int(channels) < 1) or (int(channels) > 3)):
#                print("Keysight E36312A Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channels))
#                return
#            self.powerSupplyDevice.write(":OUTP OFF,(@{})".format(channels))
#            if (self.get_on_off(channels) != False):
#                   print("Keysight E36312A Error --> Tried to turn off Channel {} of the Rigol DP832, but it didn't turn off".format(channels))
#            
#        else:
#            for i in channels:
#                if ((int(i) < 1) or (int(i) > 3)):
#                    print("Keysight E36312A Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(i))
#                    return
#                
#            for i in channels:
#               self.powerSupplyDevice.write(":OUTP OFF,(@{})".format(i))
#               if (self.get_on_off(i) != False):
#                   print("Keysight E36312A Error --> Tried to turn off Channel {} of the Rigol DP832, but it didn't turn off".format(i))
#    
#    #Get channel status
#    def get_on_off(self, channel):
#        self.powerSupplyDevice.write(":OUTP? (@{})".format(channel))
#        resp = self.powerSupplyDevice.read().strip()
#        status = None
#        if (resp == "1"): #ON
#            status = True
#        elif (resp == "0"): #OFF
#            status = False
#        return (status)
#    
#    #Set voltage output of a channel
#    def set_channel(self, channel, voltage = None, current = 1):        
#        if (voltage):
#            if ((voltage > 0) and (voltage < 30)):
#                self.powerSupplyDevice.write(":APPL CH{},{},{}".format(channel,voltage,current))      
#                self.powerSupplyDevice.write(":SOUR:VOLT? (@{})".format(channel))
#                response = float(self.powerSupplyDevice.read().strip())
#                if (response != voltage):
#                    print("RigolDP832 Error --> Voltage was set to {}, but response is {}".format(voltage, response))
#            else:
#                print("Keysight E36312A Error --> Voltage must be between 0 and 30 Volts, was {}".format(voltage))
#        else:
#            print("Keysight E36312A Error --> Not able to set channel voltage" )
#
#                
#    #Returns array of the 3 power supply voltages
#    def measure_voltages(self):   
#        self.powerSupplyDevice.write(":MEAS:VOLT? (@1,2,3)")
#        response = (self.powerSupplyDevice.read().strip().split(","))
#        for i in range(len(response)):
#            response[i] = float(response[i])
#        return response
#    
#    def measure_currents(self):   
#        self.powerSupplyDevice.write(":MEAS:CURR? (@1,2,3)")
#        response = (self.powerSupplyDevice.read().strip().split(","))
#        for i in range(len(response)):
#            response[i] = float(response[i])
#        return response
#

    #__INIT__#
    def __init__(self):
        self.ADDR = u'USB0::0xF4EC::0xEE38::T0105C20190045::0::INSTR'

a = PS_CTL()
a.ps_init()
