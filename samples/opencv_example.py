from pymba import *
import numpy as np
import cv2
import time

now = time.time()
#very crude example, assumes your camera is PixelMode = BAYERRG8

# start Vimba
with Vimba() as vimba:
    # get system object
    system = vimba.getSystem()

    # list available cameras (after enabling discovery for GigE cameras)
    if system.GeVTLIsPresent:
        system.runFeatureCommand("GeVDiscoveryAllOnce")
        time.sleep(0.2)
    cameraIds = vimba.getCameraIds()
    for cameraId in cameraIds:
        print 'Camera ID:', cameraId

    # get and open a camera
    camera0 = vimba.getCamera(cameraIds[0])
    camera0.openCamera()

    # list camera features
    cameraFeatureNames = camera0.getFeatureNames()
    for name in cameraFeatureNames:
        print 'Camera feature:', name

    # read info of a camera feature
    featInfo = camera0.getFeatureInfo('AcquisitionMode')
    for field in featInfo.getFieldNames():
        print field, '--', getattr(featInfo, field)
    featInfo = camera0.getFeatureInfo('PixelFormat')
    for field in featInfo.getFieldNames():
        print field, '--', getattr(featInfo, field)

    # get the value of a feature
    print camera0.AcquisitionMode
    print camera0.ExposureTimeAbs
    expotime=camera0.ExposureTimeAbs
    # set the value of a feature
    camera0.AcquisitionMode = 'SingleFrame'
    camera0.PixelFormat = 'Mono8'

    # create new frames for the camera
    frame0 = camera0.getFrame()    # creates a frame
    #frame1 = camera0.getFrame()    # creates a second frame

    # announce frame
    frame0.announceFrame()
    timerecord=[]
    # capture a camera image
    count = 0
    try:
        while count < 2400:
            #frame0.waitFrameCapture(1000)
            camera0.startCapture()
            frame0.queueFrameCapture()
            camera0.runFeatureCommand('AcquisitionStart')
            camera0.runFeatureCommand('AcquisitionStop')
            frame0.waitFrameCapture(1000)
                                                                
            # get image data...
            imgData = frame0.getBufferByteData()
            nowi=time.time()
            timerecord.append(nowi)
            moreUsefulImgData = np.ndarray(buffer = imgData,
                                           dtype = np.uint8,
                                           shape = (frame0.height,
                                                    frame0.width,
                                                        1))
            rgb = cv2.cvtColor(moreUsefulImgData, cv2.COLOR_BAYER_RG2RGB)
            cv2.imwrite('20160512_02rads_{}.png'.format(count), rgb)
            print "image {} saved".format(count)
            count += 1
            print count,"-", nowi-now,"s - ", count/(nowi-now)
            camera0.endCapture()
    except KeyboardInterrupt:
            print('Stopped.')
            camera0.endCapture()
            pass
    # clean up after capture
    camera0.revokeAllFrames()

    # close camera
    camera0.closeCamera()
    
from pymanip import Session
MI=Session('20160512_02_mi')
MI.save_dataset('timerecord')
MI.save_parameter('expotime')
MI.save_parameter('now')
MI.Stop()

timerecordarray=np.array(timerecord)
fic=open('20160512_02_log.txt','w')
timerecordarray.tofile(fic,sep=' ')
fic.close()
#%%
#import matplotlib.image as mpimg
#import matplotlib.pyplot as plt
#import numpy as np

#image = mpimg.imread('essai609png.png')

#plt.figure(2)
#plt.plot(timerecord,'ro')
#plt.show()

#%%
#plt.figure(1)
#imgplot = plt.imshow(moreUsefulImgData.squeeze())
#imgplot.set_cmap('gray')
