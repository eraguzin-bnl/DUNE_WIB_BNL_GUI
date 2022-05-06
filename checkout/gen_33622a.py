# -*- coding: utf-8 -*-
"""
File Name: gen_33622a.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 12/22/2017 11:11:14 AM
Last modified: 4/19/2022 6:10:24 PM
"""

#defaut setting for scientific caculation
#import numpy
#import scipy
#from numpy import *
#import numpy as np
#import scipy as sp
#import pylab as pl


import struct
import sys 
import string
import time
import copy

import visa
from visa import VisaIOError

class GEN_CTL:
    def gen_init(self):
        rm = visa.ResourceManager()
        rm_list = rm.list_resources()
        try:
            rm_list.index(self.ADDR)
            print ("Keysignt 33622A generaotr (%s) is locacted"%self.ADDR)
        except ValueError:
            print ("Keysignt 33622A generaotr (%s) is not found, Please check!"%self.ADDR)
            print ("Exit anyway!")
            sys.exit()
        try:
            gen = rm.open_resource(self.ADDR)
        except VisaIOError:
            print ("Keysight Initialize--> Exact system name not found")
            print ("Exit anyway!")
            sys.exit()
        self.gen = gen

    def gen_set(self, chn, wave_type, freq, amp, dc_oft, load="INF"):
        self.gen.write('Output{}:Load {}'.format(chn, load))
        cmd_str = 'Source{}:Apply:{} {},{},{}'.format(chn,wave_type, freq, amp, dc_oft)
        print (cmd_str)
        self.gen.write(cmd_str)
        rb_cmd_str = self.gen.query('Source{}:Apply?'.format(chn))
        print ("Write: CHN{},Wave_type={}, freq={}, amp={}, dc_oft={}, load={}".format(chn, wave_type, freq, amp, dc_oft, load))
        print ("Readback: " + rb_cmd_str)
        rb_cmd_str = self.gen.query('Source{}:Apply?'.format(1))
        print ("Readback: " + rb_cmd_str)

    def gen_chn_sw(self, chn, SW="OFF"):
        self.gen.write('Output{} {}'.format(chn, SW))
        rb_sw = self.gen.query_ascii_values("Output{}?".format(chn))
        print ("CHN{}, SW_write = {}, SW_readback = {}".format(chn, SW, rb_sw))

    def gen_set_phase(self, chn, phase):
        #cmd_str = 'Source{}:PHAS ANGL SEC {}'.format(chn, phase)
        cmd_str = 'Source{}:PHASe {}'.format(chn, phase)
        self.gen.write(cmd_str)
        rb_cmd_str = self.gen.query('Source{}:PHASe?'.format(chn))
        print ("Write: CHN{},Phase={}s".format(chn, phase))
        print ("Readback: " + rb_cmd_str)

    def gen_set_amp(self, chn, amp, oft):
        #cmd_str = 'Source{}:PHAS ANGL SEC {}'.format(chn, phase)
        cmd_str = 'Source{}:VOLTage {}'.format(chn, amp)
        self.gen.write(cmd_str)
        cmd_str = 'Source{}:VOLTage:OFFSet {}'.format(chn, oft)
        self.gen.write(cmd_str)
        #print ("Readback: " + rb_cmd_str)

    #__INIT__#
    def __init__(self):
        #self.ADDR = u'USB0::0x0957::0x5707::MY53801762::INSTR'
        #self.ADDR = u'USB0::0x0957::0x5707::MY53802435::INSTR'
        #self.ADDR = u"USB0::0x0957::0x5707::MY53802435::0::INSTR"
        self.ADDR = u"USB0::0x0957::0x5707::MY53801762::INSTR"
        self.gen = None
#a = GEN_CTL()
#a.gen_init()
#a.gen_set(chn=1, wave_type="SQU", freq=62500000/64, amp=2.5, dc_oft=1.25, load="INF")
#a.gen_chn_sw(chn=1, SW="OFF")
#time.sleep(2)
#a.gen_chn_sw(chn=1, SW="ON")
###
#a.gen_set_phase(chn=1, phase = 2.5*(1E-7))
#a.gen_set_amp(chn=1, amp=0.07, oft=0.1)
##a.gen_set_amp(chn=2, amp=0.2, oft=0.1)
##a.gen_set_phase(2, 2e-8)
#rb_cmd_str = a.gen.query('Source{}:Apply?'.format(2))
#print ("Readback: " + rb_cmd_str)

