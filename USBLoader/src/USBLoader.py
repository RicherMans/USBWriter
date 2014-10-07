'''
Created on Oct 6, 2014

@author: richman
'''

import dbus
import subprocess
import sys
import shutil
import tempfile
import hashlib
import os
from os.path import normpath, walk, isdir, isfile, dirname, basename, \
    exists as path_exists, join as path_join

formattingmap = {
                 'ntfs':'mkfs.ntfs',
                 'fat32':'mkfs.fat'
                 } 

 
def checkRoot():
    euid = os.geteuid()
    if euid != 0:
        print "This script must be run as root!"
        args = ['sudo', sys.executable] + sys.argv + [os.environ]
        os.execlpe('sudo', *args)

def checkMounts():
    ret = []
    bus = dbus.SystemBus() 
    ud_manager_obj = bus.get_object('org.freedesktop.UDisks2', '/org/freedesktop/UDisks2') 
    om = dbus.Interface(ud_manager_obj, 'org.freedesktop.DBus.ObjectManager') 
    for k, v in om.GetManagedObjects().iteritems(): 
        drive_info = v.get('org.freedesktop.UDisks2.Block', {}) 
        if drive_info.get('IdUsage') == "filesystem" and not drive_info.get('HintSystem'): 
            ret.append("/dev/" + k[-4:])
    return ret

def formatDevices(devices, formattype,labelname=None):
    for device in devices:
        if formatDevice(device, formattype,labelname) != 0:
            raise IOError("Formatting device %s , had an error !" % (device))
        
def unmount(device):
    return subprocess.call(['umount', device])
    
def isMounted(device):
    p, err = subprocess.Popen(['df', '-h'], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
    return p.find(device) != -1

def tmpMount(device):
    tmpmountpoint = tempfile.mkdtemp()
    subprocess.call(['mount', device, tmpmountpoint])
    return tmpmountpoint

def path_checksum(paths):
    """
    Recursively calculates a checksum representing the contents of all files
    found with a sequence of file and/or directory paths.

    """
    if not hasattr(paths, '__iter__'):
        raise TypeError('sequence or iterable expected not %r!' % type(paths))

    def _update_checksum(checksum, dirname, filenames):
        for filename in sorted(filenames):
            path = path_join(dirname, filename)
            if isfile(path):
                print path
                fh = open(path, 'rb')
                while 1:
                    buf = fh.read(4096)
                    if not buf : break
                    checksum.update(buf)
                fh.close()

    chksum = hashlib.sha1()

    for path in sorted([normpath(f) for f in paths]):
        if path_exists(path):
            if isdir(path):
                walk(path, _update_checksum, chksum)
            elif isfile(path):
                _update_checksum(chksum, dirname(path), basename(path))

    return chksum.hexdigest()

def copyAndMount(data, devices):
    for device in devices:
        mountdir = ""
        if not isMounted(device):
            mountdir = tmpMount(device)
            print "Device is not mounted, temporarly mount device on %s" % (mountdir)
        print "Copying files onto %s" % (device)
        chksum1 = path_checksum(os.listdir(data))
        copytree(data, mountdir)
        chksum2= path_checksum(os.listdir(mountdir))
        print "Device %s finished, unmounting ..." % (device)
        unmount(device)
        print "Checking checksums ... "
        if chksum1 != chksum2:
            raise IOError("Checksums not identical, error when transferring the files!")
            return
        
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)        

def formatDevice(device, formattype,labelname):
    if device is None:
        return
#     Somehow the os.path.ismount doesnt work
    if isMounted(device):
        print "Device %s is mounted .. unmounting" % (device)
#         Unmount
        if unmount(device) != 0:
            raise IOError("Return value of unmounting was nonzero")
        print "Unmounted!"
    print "Formatting device %s into %s format " % (device, formattype)
    p =None
    if labelname:
        p = subprocess.call([formattingmap[formattype], '-f', device ,'-L',labelname], stdout=None, stderr=None)
    else:
        p = subprocess.call([formattingmap[formattype], '-f', device], stdout=None, stderr=None)
    return p
