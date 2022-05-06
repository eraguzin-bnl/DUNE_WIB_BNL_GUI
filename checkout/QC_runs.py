# -*- coding: utf-8 -*-
"""
File Name: cls_udp.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/20/2019 4:52:43 PM
Last modified: 4/29/2022 2:49:38 PM
"""

import numpy as np
import sys
import os
import string
import time
from datetime import datetime
from cls_udp import CLS_UDP
from tcp_cfg import TCP_CFG
import struct
from raw_convertor import RAW_CONV
import matplotlib.pyplot as plt
import h5py
import pickle
from gen_33622a import GEN_CTL
import datetime
import copy
import shutil

class QC_runs( ):
    def __init__(self):
        super().__init__()
        self.tcp = TCP_CFG()
        self.udp = CLS_UDP()
        self.conv = RAW_CONV()
        self.gen = GEN_CTL()
        self.gen.gen_init()
        self.logs = {}
        self.root = "D:/IO_1826_1B/QC/"
        self.save_dir = None

    def FEMB_CHKOUT_Input(self):
        print ("Check WIB status")
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))
        
        print ("Connect FEMB to WIB Slot0")
        tester = input ("please input your name: ")
        femb_sn = int(input ("please input FEMB SN (000-999): "))
        env_cs = input("Test is performed at cold(LN2) (Y/N)? :")
        if ("Y" in env_cs) or ("y" in env_cs):
            env = "LN"
        else:
            env = "RT"
        ToyTPC_en = input("ToyTPC at FE inputs (Y/N) : ")
        note = input("A short note (<200 letters):")
        if ("Y" in ToyTPC_en) or ("y" in ToyTPC_en):
            toytpc = "150pF"
        else:
            toytpc = "0pF"
        save_dir = self.root + "FEMB{:03d}_{}_{}/".format(femb_sn, env, toytpc)
        if (os.path.exists(save_dir)):
            print ("Folder exist, please check the entering infomation...")
            #exit_en = input("Exit and Restart(Y/N)? : ")
            exit_en = "n"
            if ("Y" in exit_en) or ("y" in exit_en):
                exit()
            else:
                i = 0
                while (True):
                    i = i + 1
                    fd_new = save_dir[:-1]+"_R{:03d}/".format(i)
                    if (os.path.exists(fd_new)):
                        pass
                    else:
                        try:
                            os.makedirs(fd_new)
                        except OSError:
                            print ("Error to create folder %s"%fd_new)
                            sys.exit()    
                        save_dir = fd_new
                        break
        else:
            try:
                os.makedirs(save_dir)
            except OSError:
                print ("Error to create folder %s"%save_dir)
                sys.exit()    
        self.logs["FEMB_SN"] = femb_sn
        self.logs["Env"] = env 
        self.logs["Cd"] = toytpc 
        self.logs["Tester"] =  tester
        self.logs["Note"] = note 
        self.save_dir = save_dir
        self.logs["save_dir"]  = self.save_dir


    def pwr_info_print(self, pwr_info):
        print ("V(FE)={:.3f}V, I(FE)={:.3f}A".format(pwr_info[0][0], pwr_info[0][1]))
        print ("V(ADC)={:.3f}V, I(ADC)={:.3f}A".format(pwr_info[1][0], pwr_info[1][1]))
        print ("V(CD)={:.3f}V, I(CD)={:.3f}A".format(pwr_info[2][0], pwr_info[2][1]))
        print ("V(BIAS)={:.3f}V, I(BIAS)={:.3f}A".format(pwr_info[3][0], pwr_info[3][1]))

    def pwr_chk(self, pwr_info, v_fe, v_adc, v_cd, v_bias, iref_fe, iref_adc, iref_cd, iref_bias):
        pwr_en = 1
        if abs(v_fe - pwr_info[0][0] ) > 0.2 :
            print ("Power rail for FE, set={}V, read={}V, please check connection".format(v_fe, pwr_info[0][0]))
            pwr_en = 0
        if abs(v_adc - pwr_info[1][0] ) > 0.2 :
            print ("Power rail for ADC, set={}V, read={}V, please check connection".format(v_fe, pwr_info[1][0]))
            pwr_en = 0
        if abs(v_cd - pwr_info[2][0] ) > 0.2 :
            print ("Power rail for CD, set={}V, read={}V, please check connection".format(v_fe, pwr_info[2][0]))
            pwr_en = 0
        if abs(v_bias - pwr_info[3][0] ) > 0.2 :
            print ("Power rail for BIAS, set={}V, read={}V, please check connection".format(v_fe, pwr_info[3][0]))
            pwr_en = 0
        
        if abs(iref_fe - pwr_info[0][1] ) > 0.3 :
            print ("Power rail for FE, current of range, ref={}A, read={}A, please check connection".format(iref_fe, pwr_info[0][1]))
            pwr_en = 0
        if abs(iref_adc - pwr_info[1][1] ) > 0.3 :
            print ("Power rail for ADC, current of range, ref={}A, read={}A, please check connection".format(iref_adc, pwr_info[1][1]))
            pwr_en = 0
        if abs(iref_cd - pwr_info[2][1] ) > 0.1 :
            print ("Power rail for CD, current of range, ref={}A, read={}A, please check connection".format(iref_cd, pwr_info[2][1]))
            pwr_en = 0
        if abs(iref_bias - pwr_info[3][1] ) > 0.1 :
            print ("Power rail for BIAS, current of range, ref={}A, read={}A, please check connection".format(iref_bias, pwr_info[3][1]))
            pwr_en = 0
        return pwr_en

    def femb_initpwr_chk(self, femb_no = 0,v_fe=3.0, v_adc=3.5, v_cd=2.8, v_bias=5.0, iref_fe=0.42, iref_adc=1.29, iref_cd=0.18, iref_bias=0.05 ): 
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))

        print ("power check...")
        self.tcp.femb_pwr_set(femb=femb_no, pwr_on=0)
        time.sleep(2)
        self.tcp.femb_pwr_set(femb=femb_no, pwr_on=1, v_fe=v_fe, v_adc=v_adc, v_cd=v_cd)
        time.sleep(5)
        self.tcp.set_fe_board(sts=0,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=0,dac=0x0)
        self.tcp.femb_cfg()
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        time.sleep(2)
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        pwr_en = self.pwr_chk(pwr_info, v_fe, v_adc, v_cd, v_bias, iref_fe, iref_adc, iref_cd, iref_bias)
        if pwr_en ==0 :
            self.tcp.femb_pwr_set(femb=femb_no, pwr_on=0)
            print ("Turn FEMB off and exit...")
            exit()
        else:
            print ("FEMB power consumption is in the normal range")
        self.logs["power_vfe_ref"] =  (v_fe,  iref_fe)
        self.logs["power_vadc_ref"] = (v_adc, iref_adc)
        self.logs["power_vcd_ref"] =  (v_cd,  iref_cd,)
        self.logs["power_bias_ref"] = (v_bias,iref_bias)
        self.logs["power_init_vfe_meas"] =  pwr_info[0]
        self.logs["power_init_vadc_meas"] = pwr_info[1]
        self.logs["power_init_vcd_meas"] =  pwr_info[2]
        self.logs["power_init_bias_meas"] = pwr_info[3]

    def femb_pwr_meas (self, femb_no=0, v_fe=3.0, v_adc=3.5, v_cd=2.8, v_bias=5.0 ): 
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))

        print ("power measurment starts...")
        self.tcp.femb_pwr_set(femb=femb_no, pwr_on=1, v_fe=v_fe, v_adc=v_adc, v_cd=v_cd)
        time.sleep(2)

        print ("Measure 1: Single-ended interface between ADC and FE")
        print ("Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SDC off")
        self.logs["power_meas1_note"] = "Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SDC off"
        self.tcp.set_fe_board(sts=0,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=0,dac=0x0)
        self.tcp.femb_cfg()
        time.sleep(1)
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        self.pwr_info_print(pwr_info)
        self.logs["power_meas1_vfe_meas"] =  pwr_info[0]
        self.logs["power_meas1_vadc_meas"] = pwr_info[1]
        self.logs["power_meas1_vcd_meas"] =  pwr_info[2]
        self.logs["power_meas1_bias_meas"] = pwr_info[3]

        print ("Measure 2: Single-ended (SDC on) interface between ADC and FE")
        print ("Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SDC on")
        self.logs["power_meas2_note"] = "Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SDC on"
        self.tcp.set_fe_board(sts=0,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=0,dac=0x0, sdf=1)
        self.tcp.femb_cfg()
        time.sleep(1)
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        self.pwr_info_print(pwr_info)
        self.logs["power_meas2_vfe_meas"] =  pwr_info[0]
        self.logs["power_meas2_vadc_meas"] = pwr_info[1]
        self.logs["power_meas2_vcd_meas"] =  pwr_info[2]
        self.logs["power_meas2_bias_meas"] = pwr_info[3]

        print ("Measure 3: Differential interface between ADC and FE")
        print ("Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SEDC on")
        self.logs["power_meas3_note"] = "Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SEDC on"
        self.tcp.set_fe_board(sts=0,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=0,dac=0x0, sdd=1)
        for i in range(8):
            self.tcp.adcs_paras[i][1] = 1
        self.tcp.femb_cfg()
        time.sleep(1)
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
        self.pwr_info_print(pwr_info)
        self.logs["power_meas3_vfe_meas"] =  pwr_info[0]
        self.logs["power_meas3_vadc_meas"] = pwr_info[1]
        self.logs["power_meas3_vcd_meas"] =  pwr_info[2]
        self.logs["power_meas3_bias_meas"] = pwr_info[3]
        for i in range(8):
            self.tcp.adcs_paras[i][1] = 0


    def femb_pwr_cycles (self, femb_no=0, cycles = 5, v_fe=3.0, v_adc=3.5, v_cd=2.8, v_bias=5.0 ): 
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))

        if "LN" not in self.logs["Env"] :
            print ("Test is at room temperature, ignore power cycle test")
        else:
            print ("power cycles...")
            self.tcp.femb_pwr_set(femb=femb_no, pwr_on=0, v_fe=v_fe, v_adc=v_adc, v_cd=v_cd)
            time.sleep(1)

            hdf_dir = self.create_folder(sub_folder = "PWR")

            for i in range(cycles):
                print ("Cycle {} of {}".format(i, cycles))
                pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
                pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
                self.pwr_info_print(pwr_info)
                while (True):
                    self.tcp.femb_pwr_set(femb=femb_no, pwr_on=0, v_fe=v_fe, v_adc=v_adc, v_cd=v_cd)
                    time.sleep(1)
                    pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
                    pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
                    if (pwr_info[0][0] < 0.5) and (pwr_info[1][0] < 0.5) and (pwr_info[2][0] < 0.5) and (pwr_info[3][0] < 3) :
                        print ("FEMB is turned off")
                        self.logs["power_cycle{}_off_vfe_meas".format(i)] =  pwr_info[0]
                        self.logs["power_cycle{}_off_vadc_meas".format(i)] = pwr_info[1]
                        self.logs["power_cycle{}_off_vcd_meas".format(i)] =  pwr_info[2]
                        self.logs["power_cycle{}_off_bias_meas".format(i)] = pwr_info[3]

                        break
                    else:
                        print ("Wait until completely shut down")
                        time.sleep(1)
                print ("Turn FEMB on")
                self.tcp.femb_pwr_set(femb=femb_no, pwr_on=1, v_fe=v_fe, v_adc=v_adc, v_cd=v_cd)
                time.sleep(2)
                note = "Start FEMB configuration: 14mV/fC, 2.0us, 900mV BL, single-ended, 500pA, ASICDAC=0x10, Cali_enable, SDC off"
                self.logs["power_cycle{}_note".format(i)] = note
                self.tcp.set_fe_reset()
                self.tcp.set_fe_board(sts=1,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=1,dac=0x10)
                self.tcp.femb_cfg()
                self.tcp.cd_fe_cali()
                self.tcp.fc_act_cal() #enalbe LArASIC calibration
                time.sleep(0.1)
                fp = hdf_dir + "power_cycle{}_".format(i) +"CHK_response_SE.h5"
                femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en=True ) 
                time.sleep(0.5)
                pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
                pwr_info = self.tcp.femb_pwr_rd(femb=femb_no)
                self.logs["power_cycle{}_on_vfe_meas".format(i)] =  pwr_info[0]
                self.logs["power_cycle{}_on_vadc_meas".format(i)] = pwr_info[1]
                self.logs["power_cycle{}_on_vcd_meas".format(i)] =  pwr_info[2]
            self.logs["power_cycle{}_on_bias_meas".format(i)] = pwr_info[3]

    def femb_mons (self, femb_no=0 ): 
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))

        print ("Monitor Start...")
        print ("Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SDC off")
        self.logs["power_monitor_note"] = "Start FEMB configuration: 14mV/fC, 900mV BL, 2.0us, single-ended, 500pA, ASICDAC=0x00, Cali_disable, SDC off"
        self.tcp.set_fe_board(sts=0,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=0,dac=0x0)
        self.tcp.femb_cfg()

        adc_dft_paras = copy.deepcopy(self.tcp.adcs_paras)
        print ("ADC reference calibration...")
        for vref in range (0x1f, 0x100, 0x40):
            for chipi in range(8):
                self.tcp.adcs_paras[chipi][3] = vref
                self.tcp.adcs_paras[chipi][4] = vref
                self.tcp.adcs_paras[chipi][5] = vref
                self.tcp.adcs_paras[chipi][6] = vref
            for asic in [0]:
                print ("Measure ASIC {} with Vref set to {:02x}".format(asic, vref))
                tmp = self.tcp.femb_adc_mon_cs(femb_no=femb_no, adc_no=asic)
                self.logs["Vref0x{:02x}_ADC{:02d}_SetRef".format(vref,asic)] = tmp[1]
                self.logs["Vref0x{:02x}_ADC{:02d}_MeasRef".format(vref,asic)] = tmp[0]
                tmp = self.tcp.femb_fe_mon_cs(femb_no=femb_no, ext_lemo=0, rst_fe=1, mon_type=2, mon_chip = asic)
                self.logs["Vref0x{:02x}_Mon_LArASIC{:02d}_BGR".format(vref,asic)] = tmp
                tmp = self.tcp.femb_fe_mon_cs(femb_no=femb_no, ext_lemo=0, rst_fe=1, mon_type=1, mon_chip = asic)
                self.logs["Vref0x{:02x}_Mon_LArASIC{:02d}_Temperature".format(vref,asic)] = tmp
        self.tcp.adcs_paras = adc_dft_paras 

        for asic in range(8):
            print ("Measure ASIC {}".format(asic))
            tmp = self.tcp.femb_adc_mon_cs(femb_no=femb_no, adc_no=asic)
            self.logs["ADC{:02d}_SetRef".format(asic)] = tmp[1]
            self.logs["ADC{:02d}_MeasRef".format(asic)] = tmp[0]
            tmp = self.tcp.femb_fe_mon_cs(femb_no=femb_no, ext_lemo=0, rst_fe=1, mon_type=2, mon_chip = asic)
            self.logs["Mon_LArASIC{:02d}_BGR".format(asic)] = tmp
            tmp = self.tcp.femb_fe_mon_cs(femb_no=femb_no, ext_lemo=0, rst_fe=1, mon_type=1, mon_chip = asic)
            self.logs["Mon_LArASIC{:02d}_Temperature".format(asic)] = tmp


        for asic in range(8):
            print ("Measure DAC of LArASIC {}".format(asic))
            if "LN" not in self.logs["Env"] :
                sgs = ["14_0mVfC" ]
            else:
                sgs = ["14_0mVfC", "25_0mVfC", "7_8mVfC", "4_7mVfC" ]

            for sgi in range(len(sgs)):
                sg0 = sgi%2
                sg1 = sgi//2
                #for vdac in range(0x40):
                for vdac in (0x00, 0x20, 0x3f):
                    tmp = self.tcp.femb_fedac_mon_cs(femb_no=femb_no, ext_lemo=0, rst_fe=1, mon_chip = asic, sgp=False, sg0=sg0, sg1=sg1, vdac=vdac )
                    self.logs["Mon_LArASIC{}_{}_DAC{:02x}".format(asic, sgs[sgi], vdac)] = tmp

        if False:
            sncs = ["900mVBL", "200mVBL"]
            print ("Measure Baseline of LArASIC")
            for snc in range(2):
                for asic in range(8):
                    for chni in range(16):
                        tmp = self.tcp.femb_fe_mon_cs(femb_no=femb_no, ext_lemo=0, rst_fe=1, mon_type=0, mon_chip = asic, mon_chipchn=chni, snc=snc, sg0=0, sg1=0 )
                        self.logs["Mon_LArASIC{}_CH{}_BL{}".format(asic, chni, sncs[snc])] = tmp

    def create_folder (self, sub_folder):
        subdir = self.save_dir + sub_folder + "/"
        if (os.path.exists(subdir)):
            shutil.rmtree(subdir)
            #exit_en = input("Folder exist. Exit and Restart(Y/N)? : ")
            #if ("Y" in exit_en) or ("y" in exit_en):
            #    exit()
            #else:
            #    i = 0
            #    while (True):
            #        i = i + 1
            #        fd_new = subdir[:-1]+"_R{:03d}/".format(i)
            #        if (os.path.exists(fd_new)):
            #            pass
            #        else:
            #            try:
            #                os.makedirs(fd_new)
            #            except OSError:
            #                print ("Error to create folder %s"%fd_new)
            #                sys.exit()    
            #            subdir = fd_new
            #            break
        #else:
        try:
            os.makedirs(subdir)
        except OSError:
            print ("Error to create folder %s"%subdir)
            sys.exit()    
        return subdir

    def femb_save_h5 (self, femb_no=0, fp=None, val=1000, plot_en=False, ana_chk = True, rms_en = False ): 
        time.sleep(0.2)
        if fp == None:
            print ("Wrong file path...")
            exit()
        elif os.path.isfile(fp):
            os.remove(fp)
        self.udp.get_rawdata_packets(val=1000)
        femb_data = []
        ASICs=8
        dset = [ [] for i in range(ASICs*16)]
        with h5py.File(fp, "a") as f:
            for asic in range(ASICs):
                chip_data = None
                while ( chip_data == None):
                    asic = asic & 0x0F
                    wib_asic = (((femb_no << 16) & 0x000F0000) + ((asic << 8) & 0xFF00))
                    self.udp.write_reg_wib_checked(7, 0x80000000)
                    self.udp.write_reg_wib_checked(7, wib_asic | 0x80000000)
                    self.udp.write_reg_wib_checked(7, wib_asic)
                    time.sleep(0.01)
                    data = self.udp.get_rawdata_packets(val=val)
                    chip_data = self.conv.raw_conv_feedloc(data)
                    if chip_data == None:
                        print ("no data received, rataking...")
                        time.sleep(0.1)
                    else:
                        break
                
                femb_data.append(chip_data)
                for i in range(16):
                    dset[i] = f.create_dataset('CH{}'.format(asic*16 + i), (len(chip_data[i]),), maxshape=(None,), dtype='u2', chunks=True) 
                    dset[i][:] = chip_data[i]
        ana =self.data_ana(femb_data, ana_chk, rms_en)
        if ana == False:
            return False
        self.logs[fp] = ana
        with open(fp[0:-3] + "ana.bin", 'wb') as fpana:
            pickle.dump(ana, fpana)
        if plot_en:
            self.FEMB_CHK_PLOT(ana[0],ana[1],ana[2],ana[3],ana[4],ana[5],fp)
        return femb_data

    def data_ana(self, femb_data, ana_chk = True, rms_en = False):
        chn_rmss = []
        chn_peds = []
        chn_pkps = []
        chn_pkns = []
        chn_onewfs = []
        chn_avgwfs = []
    
        for chipi in range(8):
            plsn = (len(femb_data[chipi][0])//500)-10
            if plsn > 100:
                plsn = 100
    
            for i in range(plsn):
                if i == 0:
                    avg_wf = np.array(femb_data[chipi][0][0:500])&0xffff
                else:
                    avg_wf = avg_wf + (np.array(femb_data[chipi][0][500*i:500*i+500])&0xffff)
            avg_wf = avg_wf//plsn
            posp = np.where(avg_wf == np.max(avg_wf))[0][0] + 500-50
    
            for chn in range(16):
                peddata = []
                chndata = femb_data[chipi][chn][posp:]
                one_wf = chndata[0:500]
                for i in range(plsn):
                    peddata += chndata[150 + 500*i: 500 + 500*i] 
                    if i == 0:
                        avg_wf = np.array(chndata[0:500])&0xffff
                    else:
                        avg_wf = avg_wf + (np.array(chndata[500*i:500*i+500])&0xffff)
                avg_wf = avg_wf//plsn
    
                if rms_en == True:
                    peddata = chndata 
                rms    = np.std(peddata)
                ped    = int(np.mean(peddata))
                peakp = np.max(avg_wf)
                peakn = np.min(avg_wf)            
    
                chn_rmss.append( rms   )  
                chn_peds.append( ped   )  
                chn_pkps.append( peakp )  
                chn_pkns.append( peakn )  
                chn_onewfs.append(one_wf )  
                chn_avgwfs.append(avg_wf )  
        chn_ampps = np.array(chn_pkps) - np.array(chn_peds)
        chip0_ped_mean = np.mean(chn_peds[0:16])
        chip0_amp_mean = np.mean(chn_ampps[0:16])
        if ana_chk:
            for tmpi in range(7):
                if abs(np.mean(chn_ampps[16+16*tmpi:32+16*tmpi]) -  chip0_amp_mean) > 500:
                    print ("FEMB configuration error (AMP diff), plase reconfigurate FEMB and retake data...")
                    return False
                elif abs(np.mean(chn_peds[16+16*tmpi:32+16*tmpi]) -  chip0_ped_mean) > 500:
                    print ("FEMB configuration error (Ped diff), plase reconfigurate FEMB and retake data...")
                    return False

        return chn_rmss,chn_peds, chn_pkps, chn_pkns, chn_onewfs, chn_avgwfs

    def FEMB_SUB_PLOT(self, ax, x, y, title, xlabel, ylabel, color='b', marker='.', atwinx=False, ylabel_twx = "", e=None):
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True)
        if (atwinx):
            ax.errorbar(x,y,e, marker=marker, color=color)
            y_min = int(np.min(y))-1000
            y_max = int(np.max(y))+1000
            ax.set_ylim([y_min, y_max])
            ax2 = ax.twinx()
            ax2.set_ylabel(ylabel_twx)
            ax2.set_ylim([int((y_min/16384.0)*2048), int((y_max/16384.0)*2048)])
        else:
            ax.plot(x,y, marker=marker, color=color)
    
    def FEMB_CHK_PLOT(self, chn_rmss,chn_peds, chn_pkps, chn_pkns, chn_onewfs, chn_avgwfs, fp):
    #    import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(10,6))
        fn = fp.split("/")[-1][0:-3]
        print (fn)
        ax1 = plt.subplot2grid((4, 4), (0, 0), colspan=2, rowspan=2)
        ax2 = plt.subplot2grid((4, 4), (0, 2), colspan=2, rowspan=2)
        ax3 = plt.subplot2grid((4, 4), (2, 0), colspan=2, rowspan=2)
        ax4 = plt.subplot2grid((4, 4), (2, 2), colspan=2, rowspan=2)
        chns = range(128)
        self.FEMB_SUB_PLOT(ax1, chns, chn_rmss, title="RMS Noise", xlabel="CH number", ylabel ="ADC / bin", color='r', marker='.')
        self.FEMB_SUB_PLOT(ax2, chns, chn_peds, title="Red: Pos Peak. Blue: Pedestal. Green: Neg Peak", xlabel="CH number", ylabel ="ADC / bin", color='r', marker='.')
        self.FEMB_SUB_PLOT(ax2, chns, chn_pkps, title="Red: Pos Peak. Blue: Pedestal. Green: Neg Peak", xlabel="CH number", ylabel ="ADC / bin", color='b', marker='.')
        self.FEMB_SUB_PLOT(ax2, chns, chn_pkns, title="Red: Pos Peak. Blue: Pedestal. Green: Neg Peak", xlabel="CH number", ylabel ="ADC / bin", color='g', marker='.')
        for chni in chns:
            ts = 100 
            x = (np.arange(ts)) * 0.5
            y3 = chn_onewfs[chni][25:ts+25]
            y4 = chn_avgwfs[chni][25:ts+25]
            self.FEMB_SUB_PLOT(ax3, x, y3, title="Waveform Overlap", xlabel="Time / $\mu$s", ylabel="ADC /bin", color='C%d'%(chni%9))
            self.FEMB_SUB_PLOT(ax4, x, y4, title="Averaging(100 Cycles) Waveform Overlap", xlabel="Time / $\mu$s", ylabel="ADC /bin", color='C%d'%(chni%9))
                    
        fig.suptitle(fn)
        plt.tight_layout( rect=[0.05, 0.05, 0.95, 0.95])
        fn = fp[0:-3] + ".png"
        plt.savefig(fn)
        plt.close()

    def femb_chks (self, femb_no=0 ): 
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))

        self.udp.write_reg_wib_checked(2, 0)
        time.sleep(0.05)
        self.udp.write_reg_wib_checked(2, 0)
        self.udp.write_reg_wib_checked(2, 1)
        time.sleep(0.05)
        self.udp.write_reg_wib_checked(2, 1)
        time.sleep(0.05)

        hdf_dir = self.create_folder(sub_folder = "CHK")

        #log = "Check LArASIC response with single-ended interface between FE and ADC"
        #print (log)
        #femb_data = False
        #while femb_data == False:
        #    self.logs["CHK_response_SE"] = log
        #    self.tcp.set_fe_reset()
        #    self.tcp.set_fe_board(sts=1,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=1,dac=0x10)
        #    self.logs["CHK_response_SE_FE_CFG"] = "sts=1,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=1,dac=0x10"
        #    self.tcp.femb_cfg()
        #    self.tcp.cd_fe_cali()
        #    self.tcp.fc_act_cal() #enalbe LArASIC calibration
        #    fp = hdf_dir + "CHK_response_SE.h5"
        #    femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en=True ) 

        #log = "Check LArASIC response with Differential interface between FE and ADC"
        #print (log)
        #femb_data = False
        #while femb_data == False:
        #    self.logs["CHK_response_DIFF"] = log
        #    self.tcp.set_fe_reset()
        #    self.tcp.set_fe_board(sts=1,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=1,dac=0x10, sdd=1)
        #    self.logs["CHK_response_DIFF_FE_CFG"] = "sts=1,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=1,dac=0x10, sdd=1"
        #    for i in range(8):
        #        self.tcp.adcs_paras[i][1] = 1
        #    self.tcp.femb_cfg()
        #    self.tcp.cd_fe_cali()
        #    self.tcp.fc_act_cal() #enalbe LArASIC calibration
        #    fp = hdf_dir + "CHK_response_DIFF.h5"
        #    time.sleep(0.5)
        #    femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en=True ) 
        #    for i in range(8):
        #        self.tcp.adcs_paras[i][1] = 0

        #lkc = ["500pA", "100pA", "5nA",  "1nA"]
        #for i in range(4):
        #    log = "Check LArASIC response, FE with " + lkc[i]
        #    print (log)
        #    femb_data = False
        #    while femb_data == False:
        #        self.logs["CHK_response_SE_"+lkc[i]] = log
        #        slk0 = i%2
        #        slk1 = i//2
        #        self.tcp.set_fe_reset()
        #        self.tcp.set_fe_board(sts=1,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=1,dac=0x10, slk0=slk0, slk1=slk1)
        #        self.logs["CHK_response_SE_FE_CFG_"+lkc[i]] = "sts=1,snc=0,sg0=0,sg1=0,st0=1,st1=1,swdac=1,dac=0x10, slk0={}, slk1={}".format(slk0, slk1)
        #        self.tcp.femb_cfg()
        #        self.tcp.cd_fe_cali()
        #        self.tcp.fc_act_cal() #enalbe LArASIC calibration
        #        fp = hdf_dir + "CHK_response_SE_{}.h5".format(lkc[i])
        #        if i >= 2:
        #            femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en=True, ana_chk=False ) 
        #        else:
        #            femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en=True, ana_chk=True ) 

        #sncs = ["900mVBL", "200mVBL"]
        #sgs = ["14_0mVfC", "25_0mVfC", "7_8mVfC", "4_7mVfC" ]
        #sts = ["1_0us", "0_5us",  "3_0us", "2_0us"]
        #for i in range(2):
        #    snc = i
        #    for j in range(4):
        #        sg0 = j%2
        #        sg1 = j//2
        #        for k in range(4):
        #            st0 = k%2
        #            st1 = k//2
        #            log = "Check LArASIC response, FE with {}_{}_{}".format(sncs[i], sgs[j], sts[k])
        #            print (log)
        #            femb_data = False
        #            while femb_data == False:
        #                self.logs["CHK_response_SE_{}_{}_{}".format(sncs[i], sgs[j], sts[k])] = log
        #                self.tcp.set_fe_reset()
        #                self.tcp.set_fe_board(sts=1,snc=snc,sg0=sg0,sg1=sg1,st0=st0,st1=st1,swdac=1,dac=0x10)
        #                self.logs["CHK_response_SE_FE_CFG__{}_{}_{}".format(sncs[i],sgs[j],sts[k])] = "sts=1,snc={},sg0={},sg1={},st0={},st1={},swdac=1,dac=0x10".format(snc, sg0, sg1, st0, st1)
        #                self.tcp.femb_cfg()
        #                self.tcp.cd_fe_cali()
        #                self.tcp.fc_act_cal() #enalbe LArASIC calibration
        #                fp = hdf_dir + "CHK_response_SE_{}_{}_{}.h5".format(sncs[i], sgs[j], sts[k])
        #                femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en=True ) 

        log = "Check LArASIC response with 2-bit DAC and pulse from WIB"
        print (log)
        femb_data = False
        while femb_data == False:
            self.logs["CHK_2bitDAC_WIBPLS"] = log
            self.tcp.set_fe_reset()
            self.tcp.set_fe_board(sts=1,snc=1,sg0=1,sg1=1,st0=1,st1=1,swdac=2,dac=0x00)
            self.logs["CHK_2bitDAC_WIBPLS"] = "sts=1,snc=0,sg0=1,sg1=1,st0=1,st1=1,swdac=2,dac=0x00"
            self.gen.gen_chn_sw(chn=1, SW="ON")
            self.tcp.femb_cfg()
            self.tcp.wib_cntl_cs(lemo_en = True)
            self.tcp.femb_cd_wr(c_id=3, c_page=0, c_addr=0x27, c_data=0x1f)
            self.tcp.femb_cd_wr(c_id=2, c_page=0, c_addr=0x27, c_data=0x1f)
            self.tcp.femb_cd_wr(c_id=3, c_page=0, c_addr=0x26, c_data=0x3) 
            self.tcp.femb_cd_wr(c_id=2, c_page=0, c_addr=0x26, c_data=0)
            time.sleep(2)
            fp = hdf_dir + "CHK_2bitDAC_WIBPLS.h5"
            femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en=True ) 
            self.tcp.wib_cntl_cs(lemo_en = False)
            self.gen.gen_chn_sw(chn=1, SW="OFF")
            self.tcp.femb_cd_wr(c_id=3, c_page=0, c_addr=0x26, c_data=0x2)
            self.tcp.femb_cd_wr(c_id=2, c_page=0, c_addr=0x26, c_data=0x0)
            time.sleep(1)

    def femb_asicdac_calis(self, femb_no=0 ): 
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))

        print ("ASIC-DAC Calibration Measurement...")

        if "LN" not in self.logs["Env"] :
            sncs = ["900mVBL", "200mVBL"]
            sgs = ["14_0mVfC" ]
            sts = ["1_0us", "0_5us",  "3_0us", "2_0us"]
        else:
            sncs = ["900mVBL", "200mVBL"]
            sgs = ["14_0mVfC", "25_0mVfC", "7_8mVfC", "4_7mVfC" ]
            sts = ["1_0us", "0_5us",  "3_0us", "2_0us"]

        self.udp.write_reg_wib_checked(2, 0)
        time.sleep(0.05)
        self.udp.write_reg_wib_checked(2, 0)
        self.udp.write_reg_wib_checked(2, 1)
        time.sleep(0.05)
        self.udp.write_reg_wib_checked(2, 1)
        time.sleep(0.05)

        hdf_dir = self.create_folder(sub_folder = "ASICDAC_CALI")

        for i in range(len(sncs)):
            snc = i
            if i == 0:
                vmaxdac = 0x20
            else:
                vmaxdac = 0x40
            for j in range(len(sgs)):
                sg0 = j%2
                sg1 = j//2
                if j == 0: #14mV/fC
                    ks = [0,1,2,3]
                else:
                    ks = [3] #only 2.0us
                for k in ks: 
                    st0 = k%2
                    st1 = k//2

                    print ("Peak finding, please wait...")
                    femb_data = False
                    while femb_data == False:
                        asicdac = 0x10
                        self.tcp.set_fe_reset()
                        self.tcp.set_fe_board(sts=1,snc=snc,sg0=sg0,sg1=sg1,st0=st0,st1=st1,swdac=1,dac=asicdac)
                        self.tcp.femb_cfg()
                        aps =[]
                        for pi in range(16):
                            self.tcp.cd_fe_cali(phase0x07=[pi, pi, pi, pi, pi, pi, pi, pi])
                            self.tcp.fc_act_cal() #enalbe LArASIC calibration
                            fp = hdf_dir + "CALI_{}_{}_{}_ASICDAC0x{:02x}_CD0x07v0x{:02x}.h5".format(sncs[i], sgs[j], sts[k], asicdac, pi)
                            femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en = False ) 
                            if femb_data == False:
                                break
                            self.tcp.fc_act_cal() #disable LArASIC calibration
                            ana =self.data_ana(femb_data)
                            ampps = np.array(ana[2]) - np.array(ana[1])
                            aps.append(list(ampps))
                        tmp = []
                        for tmpi in range(128):
                            tmp2=[]
                            for tmp2i in range(16):
                                tmp2.append(aps[tmp2i][tmpi])
                            tmp.append(tmp2)

                        locs =[]
                        for chi in range(128):
                            loc = np.where(tmp[chi] == np.max(tmp[chi]))[0][0]
                            locs.append(loc)

                        pis = []
                        for ptmpi in range(8):
                            pis.append(int(np.mean(locs[16*ptmpi : 16*ptmpi+16])))

                        self.tcp.cd_fe_cali(phase0x07=pis)
                        self.tcp.fc_act_cal() #enalbe LArASIC calibration
                        print ("Phase for peak is programmed") 

                        print ("Calibration ...")
                        for asicdac in range(0, vmaxdac, 4):
                            log = "ASICDAC_Calibration, FE with {}_{}_{}_ASICDAC0x{:02x}".format(sncs[i], sgs[j], sts[k], asicdac)
                            print (log)
                            self.logs["CALI_{}_{}_{}_ASICDAC0x{:02x}".format(sncs[i], sgs[j], sts[k], asicdac)] = log
                            self.tcp.set_fe_reset()
                            self.tcp.set_fe_board(sts=1,snc=snc,sg0=sg0,sg1=sg1,st0=st0,st1=st1,swdac=1,dac=asicdac)
                            self.tcp.fe_spi_prog()
                            time.sleep(0.05)
                            fp = hdf_dir + "CALI_{}_{}_{}_ASICDAC0x{:02x}.h5".format(sncs[i], sgs[j], sts[k], asicdac)
                            femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=200, plot_en = False ) 
                            if femb_data == False:
                                break

    def femb_rmss(self, femb_no=0 ): 
        hw_ver, fw_ver = self.tcp.wib_ver()
        print ("WIB HW Versiont = 0x{:04x}, SW Versiont = 0x{:04x}".format(hw_ver, fw_ver))

        print ("Noise Measurement...")
        if "LN" not in self.logs["Env"]:
            sncs = ["900mVBL", "200mVBL"]
            sgs = ["14_0mVfC"]
            #sts = ["1_0us"]
            sts = ["1_0us", "0_5us",  "3_0us", "2_0us"]
        else:
            sncs = ["900mVBL", "200mVBL"]
            sgs = ["14_0mVfC", "25_0mVfC", "7_8mVfC", "4_7mVfC" ]
            sts = ["1_0us", "0_5us",  "3_0us", "2_0us"]

        self.udp.write_reg_wib_checked(2, 0)
        time.sleep(0.05)
        self.udp.write_reg_wib_checked(2, 0)
        self.udp.write_reg_wib_checked(2, 1)
        time.sleep(0.05)
        self.udp.write_reg_wib_checked(2, 1)
        time.sleep(0.05)

        hdf_dir = self.create_folder(sub_folder = "RMS")

        femb_data = False
        while femb_data == False:
            self.tcp.set_fe_reset()
            self.tcp.femb_cfg()
            for i in range(len(sncs)):
                snc=i
                for j in range(len(sgs)):
                    sg0 = j%2
                    sg1 = j//2
                    for k in range(len(sts)):
                        st0 = k%2
                        st1 = k//2
                        log = "RMS, FE with {}_{}_{}".format(sncs[i], sgs[j], sts[k])
                        print (log)
                        self.logs["RMS_{}_{}_{}".format(sncs[i], sgs[j], sts[k])] = log
                        self.tcp.set_fe_reset()
                        self.tcp.set_fe_board(snc=snc,sg0=sg0,sg1=sg1,st0=st0,st1=st1)
                        self.tcp.fe_spi_prog()
                        time.sleep(0.05)
                        fp = hdf_dir + "RMS_{}_{}_{}.h5".format(sncs[i], sgs[j], sts[k])
                        femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, val=1000, plot_en = True, rms_en = True ) 


    def load_logs(self): 
        with open("./logs_dir.txt", 'r') as fp:
            fp_logs = fp.read()
        with open(fp_logs, 'rb') as fp:
            self.logs = pickle.load(fp)
            self.save_dir = self.logs["save_dir"] 
            print (self.save_dir)


    def dump_logs(self, tm=1 ): 
        with open(self.save_dir + "logs_tm{:03d}.bin".format(tm), 'wb') as fp:
            pickle.dump(self.logs, fp)
        if (tm ==1):
            with open("./logs_dir.txt", 'w') as fp:
                fp.write(self.save_dir + "logs_tm{:03d}.bin".format(tm))

    def close(self, femb_no=0 ): 
        self.tcp.femb_pwr_set(femb=femb_no, pwr_on=0)
        print ("Turn FEMB off")
        print ("FEMB QC is done!")



#    def femb_ext_calis(self, femb_no=0 ): 
#        print ("External Calibration Measurement...")
#        sncs = ["900mVBL", "200mVBL"]
#        sgs = ["14_0mVfC", "25_0mVfC", "7_8mVfC", "4_7mVfC" ]
#        sts = ["1_0us", "0_5us",  "3_0us", "2_0us"]
#
#        self.udp.write_reg_wib_checked(2, 0)
#        time.sleep(0.05)
#        self.udp.write_reg_wib_checked(2, 0)
#        self.udp.write_reg_wib_checked(2, 1)
#        time.sleep(0.05)
#        self.udp.write_reg_wib_checked(2, 1)
#        time.sleep(0.05)
#
#        hdf_dir = self.create_folder(sub_folder = "EXT_CALI")
#
#        for i in range(2):
#            snc = i
#            for j in [0]: #only 14.0mV/fC
#                sg0 = j%2
#                sg1 = j//2
#                for k in range(4): 
#                    st0 = k%2
#                    st1 = k//2
#                    print ("Find Peak...")
#                    gen.gen_set_amp(chn=2, amp=300,oft=150) #300mV
#                    time.sleep(0.5)
#
#
#                    print ("Collect data...")
#                    print ("need to set DAC value to a certain value")
#
#                    for ampmV in range(0, 501, 10):
#
#                        log = "ASICDAC_Calibration, FE with {}_{}_{}_ASICDAC0x{:02x}".format(sncs[i], sgs[j], sts[k], asicdac)
#                        print (log)
#                        self.logs["CALI_{}_{}_{}_ASICDAC0x{:02x}".format(sncs[i], sgs[j], sts[k], asicdac)] = log
#                        self.tcp.set_fe_reset()
#                        self.tcp.set_fe_board(sts=1,snc=snc,sg0=sg0,sg1=sg1,st0=st0,st1=st1,swdac=1,dac=asicdac)
#                        self.tcp.femb_cfg()
#                        self.tcp.cd_fe_cali()
#                        fp = hdf_dir + "CALI_{}_{}_{}_ASICDAC0x{:02x}.h5".format(sncs[i], sgs[j], sts[k], asicdac)
#                        femb_data = self.femb_save_h5 (femb_no=femb_no, fp=fp, plot_en = False ) 


