#!/usr/bin/env python
'''
You need to have KATCP and CORR installed. Get them from http://pypi.python.org/pypi/katcp and http://pypi.python.org/pypi/corr
\nAuthor: Jason Manley
'''

#Revs:
#2012-07-18 JRM New object oriented cam/cal interface.
#2011-02    JRM First release
import corr,time,numpy,struct,sys,logging, os

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    katcp.stop()
    exit()

def exit_clean():
    try:
        katcp.stop()
    except: pass
    exit()


if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('tut2b.py <ROACH_HOSTNAME_or_IP> [options]')
    p.set_description(__doc__)
    p.add_option('-a', '--attn', dest='attn', type='int',
        help='<attenuator> can be set to 1/2/3. 0 means all of them.')  
    p.add_option('-d', '--dB', dest='dB', type='int',
        help='<db> can be set between 0 and 31')  
    p.add_option('-f', '--freq', dest='freq', type='int',
        help='<db> can be set between 0 and 31') 
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a ROACH board. \nExiting.'
        exit()
    else:
        roach = args[0]

    if opts.attn == None:
        attn = 0
    else:
        attn = opts.attn

    if opts.dB == None:
        dB = 31
    else:
        dB = opts.dB

    if opts.freq == None:
        freq = 1
    else:
        freq = opts.freq

try:
    lh=corr.log_handlers.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    print('Connecting to server %s... '%(roach)),
    ip_str = '%s'%(roach)
    katcp = corr.katcp_serial.SerialClient(ip_str, timeout=3)
    time.sleep(0.2)
    print katcp.is_connected()
    time.sleep(0.2)

    if attn == 0:
        print 'Enabling ALL attenuators'
    elif attn == 1:
        print 'Enabling attenuator 1'
    elif attn == 2:
        print 'Enabling attenuator 2'
    elif attn == 3:
        print 'Enabling attenuator 3'
    else:
        print 'Not supported. Enabling ALL attenuators'
        attn = 0

    if dB < 0:
        print 'Not supported. Setting attenuation to 31 dB'
        dB = 31
    if dB > 31:
        print 'Not supported. Setting attenuation to 31 dB'
        dB = 31

    print 'Setting Ratty2 RF attenuation to (%d dB)'%dB 
    katcp.set_atten_db(attn,dB)   
    time.sleep(0.2)      
    
    if freq == 1:
        print 'Selecting RF freq range 0 - 828 MHz'
    elif freq == 2:
        print 'Selecting RF freq range 800 - 1100 MHz - Not implemented'
    elif freq == 3:
        print 'Selecting RF freq range 900 - 1670 MHz'
    elif freq == 4:
        print 'Not connected'
    else:
        print 'Not supported. Setting to RF freq range 0 - 828 MHz'
        freq = 1
    katcp.set_freq_range_switch(freq)
    time.sleep(0.2)

except KeyboardInterrupt:
    exit_clean()
except Exception as e:
    print e
    exit_fail()

exit_clean()

