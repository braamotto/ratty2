import iniparse, exceptions, socket, struct, numpy, os,scipy
"""
Library for parsing RATTY configuration files

Author: Jason Manley
"""
"""
Revs:
2013-04-19  JRM Major rework to simplify for RATTY2
2012-06-14  JRM Initial release 
"""
LISTDELIMIT = ','
PORTDELIMIT = ':'

cal_file_path = "/etc/ratty2/cal_files/"; #For development

class rattyconf:    
    def __init__(self, **kwargs):
        self.config_file = kwargs['config_file']
        #self.config_file_name = os.path.split(self.config_file)[1]
        self.cp = iniparse.INIConfig(open(self.config_file, 'rb'))
        self.config = kwargs
        self.read_common()
        self.config.update(kwargs)

    def __getitem__(self, item):
        #if item == 'sync_time':
        #    fp = open(VAR_RUN + '/' + item + '.' + self.config_file_name, 'r')
        #    val = float(fp.readline())
        #    fp.close()
        #    return val
        #elif item == 'antenna_mapping':
        #    fp = open(VAR_RUN + '/' + item + '.' + self.config_file_name, 'r')
        #    val = (fp.readline()).split(LISTDELIMIT)
        #    fp.close()
        #    return val
        #else:
        return self.config[item]

    def __setitem__(self,item,value):
        self.config[item]=value

    def has_key(self,key):
        return self.config.has_key(key)

    def file_exists(self):
        try:
            #f = open(self.config_file)
            f = open(self.config_file, 'r')
        except IOError:
            exists = False
            raise RuntimeError('Error opening config file at %s.'%self.config_file)
        else:
            exists = True
            f.close()
      #  # check for runtime files and create if necessary:
      #  if not os.path.exists(VAR_RUN):
      #      os.mkdir(VAR_RUN)
      #      #os.chmod(VAR_RUN,0o777)
      #  for item in ['antenna_mapping', 'sync_time']:
      #      if not os.path.exists(VAR_RUN + '/' + item + '.' + self.config_file_name):
      #          f = open(VAR_RUN + '/' + item + '.' + self.config_file_name, 'w')
      #          f.write(chr(0)) 
      #          f.close()
      #          #os.chmod(VAR_RUN+'/' + item,0o777)
        return exists


    def read_common(self):
        if not self.file_exists():
            raise RuntimeError('Error opening config file or runtime variables.')
        self.config['front_led_layout']=['adc_clip','adc_shutdown','fft_overflow','quantiser_overflow','new_accumulation','sync','NA','NA']
        self.config['snap_name'] = 'snap_adc'
        self.config['spectrum_bram_out_prefix'] =  'store_a'#'vacc_out'#
        
        #self.mode = self.sys_config['digital_system_parameters']['mode'].strip()
        self.config['n_chans']=32768
        self.config['n_par_streams']=4
        self.read_float('digital_system_parameters','sample_clk')
        self.read_str('digital_system_parameters','bitstream')
        self.read_int('digital_system_parameters','fft_shift')
        self.read_float('digital_system_parameters','acc_period')
        self.read_float('digital_system_parameters','adc_v_scale_factor')
        self.config['adc_low_level_warning']=-35
        self.config['adc_high_level_warning']=0
        self.config['fpga_clk']=self.config['sample_clk']/8
        self.config['adc_levels_acc_len']=65536        
        self.config['adc_type']='mkadc 1800Msps, 10b, single input'
        self.config['pfb_scale_factor']=101.0 #a scaling co-efficient corresponding to the gain through the digital filterbank

        self.config['katcp_port']=7147
        self.config['roach_ip']=struct.unpack('>I',socket.inet_aton(self.get_line('connection','roach_ip')))[0]
        self.config['roach_ip_str']=self.get_line('connection','roach_ip')
       
        self.config['rf_gain_range']=[-31.5,0,0.5] 
        self.read_int('analogue_frontend','band_sel')
        self.read_float('analogue_frontend','desired_rf_level')
        self.read_float('analogue_frontend','fe_amp')
        self.read_float('analogue_frontend','ignore_high_freq')
        self.read_float('analogue_frontend','ignore_low_freq')
#        self.read_bool('analogue_frontend','flip_spectrum')
        self.config['antenna_bandpass_calfile']=self.get_line('analogue_frontend','antenna_bandpass_calfile')
        self.config['system_bandpass_calfile']=self.get_line('analogue_frontend','system_bandpass_calfile')
        self.config['rf_atten_gain_calfiles']=[cf for cf in (self.get_line('analogue_frontend','rf_atten_gain_calfiles')).split(LISTDELIMIT)]

#        if self.get_line('analogue_frontend','rf_gain').strip() == 'auto':
#            self.config['rf_gain'] = None
#        else:  
        try:
            self.config['rf_attens'] = [float(att) for att in (self.get_line('analogue_frontend','rf_attens')).split(LISTDELIMIT)]
        except:
            pass 
        try:
            self.read_float('analogue_frontend','rf_atten')
        except:
            pass


    def write(self,section,variable,value):
        print 'Writing to the config file. Mostly, this is a bad idea. Mostly. Doing nothing.'
        return
        self.config[variable] = value
        self.cp[section][variable] = str(value)
        fpw=open(self.config_file, 'w')
        print >>fpw,self.cp
        fpw.close()

    def write_var(self, filename, value):
        fp=open(VAR_RUN + '/' + filename + '.' + self.config_file_name, 'w')
        fp.write(value)
        fp.close()

    def write_var_list(self, filename, list_to_store):
        fp=open(VAR_RUN + '/' + filename + '.' + self.config_file_name, 'w')
        for v in list_to_store:
            fp.write(v + LISTDELIMIT)
        fp.close()

    def read_int(self,section,variable):
        try:
            self.config[variable]=int(self.cp[section][variable])
        except:
            raise RuntimeError('Error reading integer %s:%s.'%(section,variable)) 

    def read_bool(self,section,variable):
        try:
            value=self.cp[section][variable].strip()
            if str(value).lower() in ("yes", "y", "true", "True", "t", "1"):
                self.config[variable]=(True)
            elif str(value).lower() in ("no",  "n", "false", "f", "False","0", "0.0", "", "none", "[]", "{}"):
                self.config[variable]=(False)
            else:
                raise RuntimeError('Error reading boolean %s:%s.'%(section,variable)) 
        except:
            raise RuntimeError('Error reading boolean %s:%s.'%(section,variable)) 

    def read_str(self,section,variable):
        try:
            self.config[variable]=self.cp[section][variable].strip()
        except:
            raise RuntimeError('Error reading string %s:%s.'%(section,variable)) 

    def get_line(self,section,variable):
        try:
            return str(self.cp[section][variable]).strip()
        except:
            raise RuntimeError('Error reading %s:%s.'%(section,variable)) 

    def read_float(self,section,variable):
        try: 
            self.config[variable]=float(self.cp[section][variable].strip())
        except:
            raise RuntimeError('Error reading float %s:%s.'%(section,variable)) 



def getDictFromCSV(filename):
        import csv
        f = open(filename)
        f.readline()
        reader = csv.reader(f, delimiter=',')
        mydict = dict()
        for row in reader:
            mydict[float(row[0])] = float(row[1])
        return mydict

def get_gains_from_csv(filename,col1='freq_hz',col2='gain_db'):
    freqs=[]
    gains=[]
    more=True
    fp=open(filename,'r')
    import csv
    fc=csv.DictReader(fp)
    while(more):
        try:
            raw_line=fc.next()
            freqs.append(numpy.float(raw_line[col1]))
            gains.append(numpy.float(raw_line[col2]))
        except:
            more=False
            break
    return freqs,gains


def cal_files(filename):
    return "%s%s"%(cal_file_path, filename)
