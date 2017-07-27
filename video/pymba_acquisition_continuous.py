from pathlib import Path
import time
import matplotlib.pyplot as plt

import numpy as np
import png

from pymba import *
from pymba.vimbaexception import VimbaException
from pymba.vimbainterface import VimbaInterface
from pymanip import Session

# Paramètres de l'acquisition
destination_dir = Path(r'C:\Users\Julien Salort\Documents\Acquis')
acquisition_name = 'essai'
images_dir = destination_dir / acquisition_name
N = 20

if not destination_dir.exists():
    destination_dir.mkdir()
if not destination_dir.is_dir():
    raise NotADirectoryError
if not images_dir.exists():
    images_dir.mkdir()
if not images_dir.is_dir():
    raise NotADirectoryError

MI = Session(images_dir, ('timestamp',))

def print_features(cam):
    cameraFeatureNames = cam.getFeatureNames()
    for name in cameraFeatureNames:
        try:
            val = cam.__getattr__(name)
            if isinstance(val, bytes):
                val = val.decode('ascii')
            info = cam.getFeatureInfo(name)
            unit = info.unit
            if isinstance(unit, bytes):
                unit = unit.decode('ascii')
            elif unit is None:
                unit = ""
            print(info.displayName.decode('ascii'),
                  '(' + name.decode('ascii') + ')',
                  ':', val, unit)
        except VimbaException:
            print(name.decode('ascii'), ': ?')
            
with Vimba() as vimba:
    print("Vimba version:", vimba.getVersion())
    system = vimba.getSystem()
    print("""
Vimba System features
=====================""")
    print_features(system)
    
    # list available cameras (after enabling discovery for GigE cameras)
    if system.GeVTLIsPresent:
        system.runFeatureCommand("GeVDiscoveryAllOnce")
        time.sleep(0.2)
        
    # Ouverture de le caméra
    cameraIds = vimba.getCameraIds()
    
    for cameraId in cameraIds:
        #print('Camera ID:', cameraId)
        cam = vimba.getCamera(cameraId)
        cam.openCamera()
        #print('Camera ID String', cam.cameraIdString)
        
    
    # Acquisition

    print("""
Camera info structure
=====================""")
    info = cam.getInfo()
    print('cameraName:', info.cameraName.decode('ascii'))
    print('interfaceIdString:', info.interfaceIdString.decode('ascii'))
    print('modelName:', info.modelName.decode('ascii'))
    print('serialString:', info.serialString.decode('ascii'))
        
    #print('Acquisition mode:', cam.AcquisitionMode)
    # Possible values: 'Continuous', 'SingleFrame', 'MultiFrame', 'Recorder'
    #cam.IIDCActivateFormat7 = True
    cam.AcquisitionMode = 'Continuous'
    cam.IIDCPhyspeed = 'S800'
    cam.PixelFormat = 'Mono16'
    
    #cam.AcquisitionFrameRate = 20.0
    cam.TriggerMode = 'On'
    
    #cam.IIDCPacketSizeAuto = 'On'
        
    print("""
Vimba Camera features
=====================""")
    print_features(cam)
    
    frame = cam.getFrame()
    frame.announceFrame()

    print("""
Acquisition
===========""")
    cam.startCapture()
    cam.runFeatureCommand('AcquisitionStart')

    for i in range(N):
        frame.queueFrameCapture()
        frame.waitFrameCapture()
        timestamp = frame.timestamp/1e7
        img = png.from_array(frame.getImage(), mode='L')
        with open(images_dir / 'img-{:03d}.png'.format(i), 'wb') as f:
            img.save(f)
        MI.log_addline()
        
    cam.runFeatureCommand('AcquisitionStop')
    cam.endCapture()
    cam.revokeAllFrames()

print('Finished.')

# Graphe des timestamps
t = MI['timestamp'][-N:]
tMI = MI['t'][-N:]
MI.Stop()
real_fs = 1/np.mean(t[1:]-t[:-1])
print('Real fs =', real_fs, 'Hz')
print('Computer estimated=', 1/np.mean(tMI[1:]-tMI[:-1]))

plt.figure()
plt.plot(t-t[0], 'bo')
plt.show()
MI.Stop()
