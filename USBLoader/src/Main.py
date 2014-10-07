'''
Created on Oct 6, 2014

@author: richman
'''
#!/usr/bin/python
 
from argparse import ArgumentParser
import USBLoader as usb
import sys
import glib
from pyudev import Context, Monitor
import time
try:
    from pyudev.glib import MonitorObserver
    def device_event(obs,observer, device):
        print 'event {0} on device {1}'.format(device.action, device)
except:
    from pyudev.glib import GUDevMonitorObserver as MonitorObserver
    def device_event(obs,action,device):
        if action == 'add':
            print 'Device {0} at {1}'.format(action,device)
            global data,formatting,labelname
#             Custom timeout... we need some time until mounting is done
            time.sleep(2)
            mountFormatCopy()
            print "Finished device %s !"%(device)
data = None
formatting = None
labelname = None
        
formats = ["ntfs","fat32"]
def parseargs():
    parser = ArgumentParser(description='Writes some data on mutliple autodetected USB devices. Be careful, they will be formatted!')
    parser.add_argument('data',help="The upper most folder which need to be transferred on all usb Sticks")
    parser.add_argument('-l','--loop',action='store_true',help='Activates the loop, which will then let the program wait for any new devices plugged in. Abort by CRTL+C')
    parser.add_argument('-f','--format',required=False,choices=["ntfs","fat32"],default=formats[0],help="Formats the sticks, default format %(default)s")
    parser.add_argument('-fl','--formatlabel',required=False,type=str,help="Formats the Devices with this Label")
    return parser.parse_args()

def loopForDevices():
    context = Context()
    monitor = Monitor.from_netlink(context)
    
    monitor.filter_by(subsystem='usb')
    observer = MonitorObserver(monitor)
    
    observer.connect('device-event', device_event)
    monitor.start()
    glib.MainLoop().run()
 
def mountFormatCopy(): 
    mounteddevices = usb.checkMounts()
    if not mounteddevices:
        print "No USB devices mounted yet/no USB devices plugged in!"
        print "Exiting ... "
        sys.exit(0)
    usb.formatDevices(mounteddevices, formatting,labelname)
    usb.copyAndMount(data,mounteddevices )
    
def main():
    usb.checkRoot()
    args = parseargs()
    global data,formatting,labelname
    data = args.data
    formatting = args.format
    labelname = args.formatlabel
    if args.loop:
        loopForDevices()
    else:
        mountFormatCopy()
    print "Finished!"

if __name__ == '__main__':
    main()