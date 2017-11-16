"""

This is the definition of a higher level PCO_Camera object
based on the low-level pco.pixelfly module.

"""

import sys
import itertools
import ctypes
import win32event

import numpy as np
import matplotlib.pyplot as plt

import pymanip.pco.pixelfly as pf

class PCO_Buffer:

    def __init__(self, cam_handle, XResAct, YResAct):
        self.cam_handle = cam_handle
        self.XResAct = XResAct
        self.YResAct = YResAct
        bufSizeInBytes = XResAct*YResAct*ctypes.sizeof(ctypes.wintypes.WORD)
        
        self.bufPtr = ctypes.POINTER(ctypes.wintypes.WORD)()
        num, event = pf.PCO_AllocateBuffer(cam_handle, -1, bufSizeInBytes, 
                                           self.bufPtr)
        self.bufNr = num
        self.event_handle = event
    
    def free(self):
        pf.PCO_FreeBuffer(self.cam_handle, self.bufNr)
        self.bufPtr = None
        
    def __enter__(self):
        return self
    
    def __exit__(self, type_, value, cb):
        self.free()
    
    def as_array(self):
        return np.ctypeslib.as_array(self.bufPtr, shape=(self.YResAct, self.XResAct))
    
class PCO_Camera:

    # Open/Close camera
    def __init__(self, board=0):
        """
        pco.sdk_manual page 10:
        First step is to PCO_OpenCamera
        As next step camera description and status should be queried
        by calling PCO_GetCameraDescription and PCO_GetCameraHealthStatus
        """
        
        self.handle = pf.PCO_OpenCamera(board)
        self.camera_description = pf.PCO_GetCameraDescription(self.handle)
        warn, err, status = self.health_status()
        if warn or err:
            print('Warning bits :', warn)
            print('Error bits :', err)
        else:
            print('Connected to camera on board', board)
            #print(str(self.camera_description))
            print('Status bits :', status)
        pf.PCO_SetBitAlignment(self.handle, sys.byteorder == 'little')
        MetaDataSize, MetaDataVersion = pf.PCO_SetMetaDataMode(self.handle, True)
        self.MetaDataSize = MetaDataSize
        self.MetaDataVersion = MetaDataVersion
    
    def close(self):
        pf.PCO_CloseCamera(self.handle)
        self.handle = None
        print('Connection to camera closed.')
    
    def __enter__(self):
        return self
        
    def __exit__(self, type_, value, cb):
        self.close()
    
    # Query states
    def health_status(self):
        warn, err, status = pf.PCO_GetCameraHealthStatus(self.handle)
        return warn, err, status
    
    # Image acquisition
    def acquisition_oneshot(self):
        """
        Simple one shot image grabbing.
        Returns an autonomous numpy array
        """
        # Arm camera
        pf.PCO_ArmCamera(self.handle)
        XResAct, YResAct, XResMax, YResMax = pf.PCO_GetSizes(self.handle)

        with PCO_Buffer(self.handle, XResAct, YResAct) as buffer:
            try:
                pf.PCO_SetImageParameters(self.handle, XResAct, YResAct,
                                          pf.IMAGEPARAMETERS_READ_WHILE_RECORDING)
                pf.PCO_SetRecordingState(self.handle, True)
                pf.PCO_GetImageEx(self.handle, 1, 0, 0, buffer.bufNr, XResAct, YResAct, 16)
                array = buffer.as_array().copy()
            finally:
                pf.PCO_SetRecordingState(self.handle, False)
                pf.PCO_CancelImages(self.handle)
        return array
    
    def acquisition(self, num=np.inf, timeout=1000):
        """
        Multiple image acquisition
        returns a shared memory numpy array valid only
        before generator object cleanup.
        """
        
        # Arm camera
        if pf.PCO_GetRecordingState(self.handle):
            pf.PCO_SetRecordingState(self.handle, False)
        pf.PCO_ArmCamera(self.handle)
        warn, err, status = self.health_status()
        if err != 0:
            raise RuntimeError('Camera has error status!')
        XResAct, YResAct, XResMax, YResMax = pf.PCO_GetSizes(self.handle)
        
        with PCO_Buffer(self.handle, XResAct, YResAct) as buf1, \
             PCO_Buffer(self.handle, XResAct, YResAct) as buf2, \
             PCO_Buffer(self.handle, XResAct, YResAct) as buf3, \
             PCO_Buffer(self.handle, XResAct, YResAct) as buf4:
            
            buffers = (buf1, buf2, buf3, buf4)
            try:
                pf.PCO_SetImageParameters(self.handle, XResAct, YResAct,
                                          pf.IMAGEPARAMETERS_READ_WHILE_RECORDING)
                pf.PCO_SetRecordingState(self.handle, True)
                for buffer in buffers:
                    pf.PCO_AddBufferEx(self.handle, 0, 0, buffer.bufNr, XResAct, YResAct, 16)
                count = 0
                buffer_ring = itertools.cycle(buffers)
                while count < num:
                    waitstat = win32event.WaitForMultipleObjects([buffer.event_handle for buffer in buffers],
                                                                 0, timeout)
                    if waitstat == win32event.WAIT_TIMEOUT:
                        raise RuntimeError('Timeout')
                    for ii, buffer in zip(range(4), buffer_ring):
                        waitstat = win32event.WaitForSingleObject(buffer.event_handle, 0)
                        if waitstat == win32event.WAIT_OBJECT_0:
                            win32event.ResetEvent(buffer.event_handle)
                            statusDLL, statusDrv = pf.PCO_GetBufferStatus(self.handle, buffer.bufNr)
                            if statusDrv != 0:
                                raise RuntimeError('buffer {:} error status {:}'.format(buffer.bufNr, statusDrv))
                            yield buffer.as_array()
                            count += 1
                            pf.PCO_AddBufferEx(self.handle, 0, 0, buffer.bufNr, XResAct, YResAct, 16)
                        else:
                            break
            finally:
                pf.PCO_SetRecordingState(self.handle, False)
                pf.PCO_CancelImages(self.handle)
            
if __name__ == '__main__':
    import matplotlib.pyplot as plt
    #with PCO_Camera() as cam:
    #    array = cam.acquisition_oneshot()
    #plt.imshow(array, origin='lower')
    #plt.colorbar()
    with PCO_Camera() as cam:
        for ii, im in enumerate(cam.acquisition(50)):
            plt.clf()
            plt.imshow(im, origin='lower')
            plt.title('img {:}'.format(ii))
            plt.colorbar()
            plt.pause(0.1)
    plt.show()
