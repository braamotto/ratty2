# -*- coding: utf-8 -*-
import numpy,scipy,scipy.interpolate,iniparse,ratty2

#2013-04-24 rf_atten and fe_amp rolled into one.
#smoothing functions from http://www.swharden.com/blog/2008-11-17-linear-data-smoothing-in-python/

c=299792458. #speed of light in m/s
#cal_file_path = "/etc/rfi_sys/cal_files/"; #For when you have everything working and ready to install with distutils
cal_file_path = "/etc/ratty2/cal_files/"; #For development
def cal_files(filename):
    return "%s%s"%(cal_file_path, filename)

def smoothList(list,strippedXs=False,degree=10):  
     if strippedXs==True: return Xs[0:-(len(list)-(len(list)-degree+1))]  
     smoothed=[0]*(len(list)-degree+1)  
     for i in range(len(smoothed)):  
         smoothed[i]=sum(list[i:i+degree])/float(degree)  
     return smoothed  

def smoothListTriangle(list,strippedXs=False,degree=5):  
     weight=[]  
     window=degree*2-1  
     smoothed=[0.0]*(len(list)-window)  
     for x in range(1,2*degree):weight.append(degree-abs(degree-x))  
     w=numpy.array(weight)  
     for i in range(len(smoothed)):  
         smoothed[i]=sum(numpy.array(list[i:i+window])*w)/float(sum(w))  
     return smoothed  

def smoothListGaussian(list,strippedXs=False,degree=5):  
     window=degree*2-1  
     weight=numpy.array([1.0]*window)  
     weightGauss=[]  
     for i in range(window):  
         i=i-degree+1  
         frac=i/float(window)  
         gauss=1/(numpy.exp((4*(frac))**2))  
         weightGauss.append(gauss)  
     weight=numpy.array(weightGauss)*weight  
     smoothed=[0.0]*(len(list)-window)  
     for i in range(len(smoothed)):  
         smoothed[i]=sum(numpy.array(list[i:i+window])*weight)/sum(weight)  
     return smoothed  

def calc_mkadc_bandpass(chans,adc_cal_file_i):
    gain_mkAdc = getDictFromCSV(adc_cal_file_i)#('/home/henno/adc_bandpass_20-890MHz_n10dBm_input_sn004.csv')
    x = numpy.arange(0,len(gain_mkAdc),1)
    y = numpy.zeros(len(gain_mkAdc))    
    for i in range(len(gain_mkAdc)-1):
        y[i] = gain_mkAdc[(i)*10.0] 
    x_int = numpy.arange(0,len(gain_mkAdc),len(gain_mkAdc)/(chans*1.0))
    bandFlat = numpy.subtract(10,numpy.interp(x_int, x, y))
    return bandFlat

def dmw_per_sq_m_to_dbuv(dbmw):
    # from http://www.ahsystems.com/notes/RFconversions.php: dBmW/m2 = dBmV/m - 115.8 
    return dbmw + 115.8

def dbuv_to_dmw_per_sq_m(dbuv):
    # from http://www.ahsystems.com/notes/RFconversions.php: dBmW/m2 = dBmV/m - 115.8 
    return dbuv - 115.8

def dbm_to_dbuv(dbm):
    return dbm+106.98

def dbuv_to_dbm(dbuv):
    return dbm-106.98 

def v_to_dbuv(v):
    return 20*numpy.log10(v*1e6)

def dbuv_to_v(dbuv):
    return (10**(dbuv/20.))/1e6

def dbm_to_v(dbm):
    return numpy.sqrt(10**(dbm/10.)/1000*50)

def v_to_dbm(v):
    return 10*numpy.log10(v*v/50.*1000)

def bitcnt(val):
    '''Counts the number of set bits in the binary value.'''
    ret_val=0
    shift_val=val
    while shift_val>=1:
        if shift_val&1: ret_val +=1
        shift_val = shift_val>>1
    return ret_val

def polyfit(freqs,gains,degree=9):
    """Just calls numpy.polyfit. Mostly here as a reminder."""
    return numpy.polyfit(freqs,gain,deg=degree)

def af_from_gain(freqs,gains):
        """Calculate the antenna factor (in dB/m) from a list of frequencies (in Hz) and gains (in dBi).
            There are a number of assumptions made for this to be valid:
             1) Far-field only (plane wave excitation).
             2) 50ohm system.
             3) antenna is polarisation matched.
             4) effects of impedance mismatch are included."""
        #From Howard's email:
        #The antenna factors are derived from gain by taking 9.73/(lambda(sqrt(Gain))  - note the gain here is the non-dB gain. It is worth noting that in dB’s the conversion is 19.8 – 20log10(lambda) – 10 log(Gain)
        #avoid the divide by zero error:
        if freqs[0]==0:
            freqs[0]=numpy.finfo(numpy.float).eps
        return 19.8 - 20*numpy.log10(c/freqs) - gains

def gain_from_af(freqs,afs):
        """Calculate the gain (in dBi) from the Antenna Factor (in dB/m)."""
        return 19.8 - 20*numpy.log10(c/freqs) - afs

def getDictFromCSV(filename):
        import csv
        f = open(filename)
        f.readline()
        reader = csv.reader(f, delimiter=',')
        mydict = dict()
        for row in reader:
            mydict[float(row[0])] = float(row[1])
        return mydict

def get_gains_from_csv(filename):
    freqs=[]
    gains=[]
    more=True
    fp=open(filename,'r')
    import csv
    fc=csv.DictReader(fp)
    while(more):
        try: 
            raw_line=fc.next()
            freqs.append(numpy.float(raw_line['freq_hz']))
            gains.append(numpy.float(raw_line['gain_db']))
        except:
            more=False
            break
    return freqs,gains

class cal:

    def __init__(self, **kwargs):
        """Either specify a config_file, or else specify
            n_chans,bandwidth, n_par_streams, bitstream, fft_shfit, adc_type, desired_rf_level, spectrum_bits, antenna_bandpass, config['system_bandpass'], config['rf_gain'] and acc_period"""
        self.config={}
        if kwargs.has_key('config_file'):
            self.config = ratty2.conf.rattyconf(**kwargs)

        for key in kwargs:
            self.config[key]=kwargs[key]
        self.config['bandwidth']=self.config['sample_clk']/2
        self.config['chan_width']=numpy.float(self.config['bandwidth'])/self.config['n_chans']
        self.config['freqs']=numpy.arange(self.config['n_chans'])*float(self.config['bandwidth'])/self.config['n_chans'] #channel center freqs   in Hz

        if (self.config['system_bandpass_calfile'] != 'none'):
            self.config['system_bandpass'] = self.get_interpolated_gains(self.config['system_bandpass_calfile'])
        else:
            self.config['system_bandpass'] = numpy.zeros(self.config['n_chans'])

        if (self.config['antenna_bandpass_calfile'] != 'none'):
            self.config['antenna_bandpass'] = self.get_interpolated_gains(self.config['antenna_bandpass_calfile'])
        else:
            self.config['antenna_bandpass'] = numpy.zeros(self.config['n_chans'])
        self.config['ant_factor'] = af_from_gain(self.config['freqs'], self.config['antenna_bandpass'])

        self.config['fft_scale']=bitcnt(self.config['fft_shift'])

        #gain_setpoints=numpy.arange(self.config['rf_gain_range'][0],self.config['rf_gain_range'][1]+self.config['rf_gain_range'][2],self.config['rf_gain_range'][2])

        #Override any defaults:
        for key in kwargs:
            self.config[key]=kwargs[key]

    def plot_bandshape(self,freqs):
        import pylab
        pylab.plot(bandshape(freqs))
        pylab.title('Bandpass calibration profile')
        pylab.xlabel('Frequency (Hz)')
        pylab.ylabel('Relative response (dB)')

    def plot_atten_gain_map(self):
        import pylab
        inputs=atten_gain_map.keys()
        inputs.sort()
        pylab.plot(inputs,[atten_gain_map[k] for k in inputs])
        pylab.title('RF attenuator mapping')
        pylab.xlabel('Requested value (dB)')
        pylab.ylabel('Actual value (dB)')
    
    def get_interpolated_gains(self,fileName):
        """Retrieves antenna gain mapping from bandpass csv files and interpolates data to return values at 'freqs'."""
        cal_freqs,cal_gains=get_gains_from_csv(cal_files(fileName))
        inter_freqs=scipy.interpolate.interp1d(cal_freqs,cal_gains,kind='linear')
        return inter_freqs(self.config['freqs'])

    def get_interpolated_attens(self,fileName,setpoint):
        cal_setpoints,cal_attens=get_gains_from_csv(cal_files(fileName))
        inter_attens=scipy.interpolate.interp1d(cal_setpoints,cal_attens,kind='linear')
        return inter_attens(setpoint)

    def plot_ant_gain(self):
        """Plots the antenna gain."""
        import pylab
        pylab.plot(self.config['freqs']/1e6,self.config['antenna_bandpass'])
        pylab.title('Antenna gain %s'%self.config['antenna_bandpass_calfile'])
        pylab.xlabel('Frequency (MHz)')
        pylab.ylabel('Relative response (dBi)')

    def plot_ant_factor(self):
        """Plots the antenna factor over the given frequencies as calculated from the specified antenna CSV file."""
        import pylab
        pylab.plot(self.config['freqs']/1e6,self.config['ant_factor'])
        pylab.title('Antenna factor as a function of frequency (%s)'%self.config['antenna_bandpass_calfile'])
        pylab.xlabel('Frequency (MHz)')
        pylab.ylabel('Antenna factor (dBuV/m)')

    def freq_to_chan(self,frequency,n_chans=None):
        """Returns the channel number where a given frequency is to be found. Frequency is in Hz."""
        if frequency<0: 
            frequency=self.config['bandwidth']+frequency
            #print 'you want',frequency
        if frequency>=self.config['bandwidth']: raise RuntimeError("that frequency is too high.")
        if n_chans==None:
            n_chans=self.config['n_chans']
        return round(float(frequency)/self.config['bandwidth']*n_chans)%n_chans

    def get_input_adc_v_scale_factor(self):
        """Provide the calibration factor to get from an ADC input voltage to the actual frontend input voltage. Does not perform any frequency-dependent calibration."""
        return 1/(10**((self.config['rf_gain'])/20.))

    def calibrate_adc_snapshot(self,raw_data):
        """Calibrates a raw ADC count timedomain snapshot. Returns ADC samples in V, ADC spectrum in dBm, input spectrum in dBm and input spectrum of n_chans in dBm."""
        ret={}
        ret['adc_raw']=raw_data
        ret['adc_v']=raw_data*self.config['adc_v_scale_factor']
        ret['input_v']=ret['adc_v']*self.get_input_adc_v_scale_factor() 
        #Calculate the spectrum:
        n_accs=len(raw_data)/self.config['n_chans']/2
        window=numpy.hamming(self.config['n_chans']*2)
        spectrum=numpy.zeros(self.config['n_chans'])
        freqs=numpy.arange(self.config['n_chans'])*float(self.config['bandwidth'])/self.config['n_chans']
        ret['freqs']=freqs
        for acc in range(n_accs):
            spectrum += numpy.abs((numpy.fft.rfft(ret['adc_v'][self.config['n_chans']*2*acc:self.config['n_chans']*2*(acc+1)]*window)[0:self.config['n_chans']])) 
        ret['adc_spectrum_dbm']  = 20*numpy.log10(spectrum/n_accs/self.config['n_chans']*6.14)
        #get config['system_bandpass']:
        #if self.config['system_bandpass_calfile'] != 'none':
        cal_freqs,cal_gains=get_gains_from_csv(cal_files(self.config['system_bandpass_calfile']))
        inter_freqs=scipy.interpolate.interp1d(cal_freqs,cal_gains,kind='linear')
        bp=inter_freqs(freqs)
        ret['system_bandpass']=bp
        #else: bp=0
        ret['input_spectrum_dbm']=ret['adc_spectrum_dbm']-bp-self.config['rf_gain']

        if self.config['antenna_bandpass_calfile'] != 'none':
            #get antenna factor:
            cal_freqs,cal_gains=get_gains_from_csv(cal_files(self.config['antenna_bandpass_calfile']))
            inter_freqs=scipy.interpolate.interp1d(cal_freqs,cal_gains,kind='linear')
            af=af_from_gain(freqs,inter_freqs(freqs))
            ret['ant_factor']=af
            ret['antenna_bandpass']=inter_freqs(freqs)
            ret['input_spectrum_dbuv'] = dbm_to_dbuv(ret['input_spectrum_dbm']) + af 
        return ret
