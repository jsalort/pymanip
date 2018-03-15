import numpy as np
from pymanip.video import MetadataArray, Camera
from pymba import Vimba
from pymba.vimbaexception import VimbaException
import asyncio

class AVT_Camera(Camera):
    # Class attributes
    system = None
    vimba = None
    active_cameras = set()
    
    @classmethod
    def get_camera_list(cls):
        if cls.vimba:
            return cls.vimba.getCameraIds()
        else:
            with Vimba() as vimba_:
                return vimba_.getCameraIds()
        
    def __init__(self, cam_num=0):
        if not AVT_Camera.vimba:
            AVT_Camera.vimba = Vimba().__enter__()
        if not AVT_Camera.system:
            AVT_Camera.system = AVT_Camera.vimba.getSystem()
        self.cameraDesc = AVT_Camera.get_camera_list()[cam_num]
        #self.info = vimba.getCameraInfo(self.cameraDesc)
        self.camera = AVT_Camera.vimba.getCamera(self.cameraDesc)
        self.camera.openCamera()
        AVT_Camera.active_cameras.add(self)
        self.num = cam_num
        self.name = 'AVT ' + str(cam_num)
    
    def close(self):
        self.camera.closeCamera()
        self.camera = None
        AVT_Camera.active_cameras.remove(self)
        if len(AVT_Camera.active_cameras) == 0:
            AVT_Camera.system = None
            AVT_Camera.vimba.__exit__(None, None, None)
            AVT_Camera.vimba = None
        
    def __exit__(self, type_, value, cb):
        super(AVT_Camera, self).__exit__(type_, value, cb)
        self.close()
    
    def camera_features(self):
        cameraFeatureNames = self.camera.getFeatureNames()
        return [f.decode('ascii') for f in cameraFeatureNames]
        
    def camera_feature_info(self, featureName):
        featureInfo = self.camera.getFeatureInfo(featureName)
        featDict = {field.decode('ascii') if isinstance(field, bytes) else field: getattr(featureInfo, field) for field in featureInfo.getFieldNames()}
        featDict['value'] = getattr(self.camera, featureName)
        featDict['range'] = self.camera.getFeatureRange(featureName)
        featDict['featureDataTypeName'] = {0: 'Unknown feature type',
                                           1: '64 bit integer',
                                           2: '64 bit floating point',
                                           3: 'Enumeration feature',
                                           4: 'String feature',
                                           5: 'Boolean feature',
                                           6: 'Command feature',
                                           7: 'Raw (direct register access) feature',
                                           8: 'Feature with no data'}[featDict['featureDataType']]
        featDict['featureFlagsStr'] = ''
        if featDict['featureFlags'] & 1:
            featDict['featureFlagsStr'] += 'r' # read access
        if featDict['featureFlags'] & 2:
            featDict['featureFlagsStr'] += 'w' # write access
        if featDict['featureFlags'] & 8:
            featDict['featureFlagsStr'] += 'v' # volatile
        if featDict['featureFlags'] & 16:
            featDict['featureFlagsStr'] += 'm' # may change after write
        for k in featDict:
            if isinstance(featDict[k], bytes):
                featDict[k] = featDict[k].decode('ascii')
        return featDict
        
    # Image acquisition
    def acquisition_oneshot(self, pixelFormat='Mono16'):
        """
        Simple one shot image grabbing.
        Returns an autonomous numpy array
        """
        self.camera.PixelFormat = pixelFormat.encode('ascii')
        self.camera.AcquisitionMode = 'SingleFrame'
        self.frame = self.camera.getFrame()
        self.frame.announceFrame()
        self.camera.startCapture()
        try:
            self.frame.queueFrameCapture()
            self.camera.runFeatureCommand('AcquisitionStart')
            self.camera.runFeatureCommand('AcquisitionStop')
            self.frame.waitFrameCapture()
            # print('timestamp =', self.frame.timestamp)
            # print('pixel_bytes =', self.frame.pixel_bytes)
            if self.frame.pixel_bytes == 1:
                dt = np.uint8
            elif self.frame.pixel_bytes == 2:
                dt = np.uint16
            else:
                raise NotImplementedError
            img = np.ndarray(buffer=self.frame.getBufferByteData(),
                           dtype=dt,
                           shape=(self.frame.height, self.frame.width)).copy()
            
        finally:
            self.camera.endCapture()
            self.camera.revokeAllFrames()
            
        return img
        
    def set_trigger_mode(self, mode=False):
        """
        True if external trigger
        """
        
        if mode:
            self.camera.TriggerMode = 'On'
            self.camera.TriggerSource = 'InputLines'
        else:
            self.camera.TriggerMode = 'Off'
                    
    async def acquisition(self, num=np.inf, timeout=1000, raw=False, pixelFormat='Mono16',
                          framerate=None, external_trigger=False, initialising_cams=None):
        """
        Multiple image acquisition
        yields a shared memory numpy array valid only
        before generator object cleanup.
        """
        self.camera.PixelFormat = pixelFormat.encode('ascii')
        self.camera.AcquisitionMode = 'Continuous'
        if framerate is not None:
            # Not usable if HighSNRIImages>0, external triggering or IIDCPacketSizeAuto are active
            self.camera.AcquisitionFrameRate = framerate
        if external_trigger:
            self.camera.TriggerMode = 'On'
            self.camera.TriggerSource = 'InputLines'
        self.frame = self.camera.getFrame()
        self.frame.announceFrame()
        self.camera.startCapture()
        self.camera.runFeatureCommand("AcquisitionStart")
        try:
            count = 0
            while count < num:
                self.frame.queueFrameCapture()
                if count == 0 and initialising_cams is not None and self in initialising_cams:
                    initialising_cams.remove(self)
                errorCode = await self.frame.waitFrameCapture_async()
                if errorCode == -12:
                    print('')
                    print('cam' + str(self.num) + ' timeout')
                    break
                elif errorCode != 0:
                    raise VimbaException(errorCode)
                if self.frame.pixel_bytes == 1:
                    dt = np.uint8
                elif self.frame.pixel_bytes == 2:
                    dt = np.uint16
                else:
                    raise NotImplementedError
                yield MetadataArray(np.ndarray(buffer=self.frame.getBufferByteData(),
                                               dtype=dt,
                                               shape=(self.frame.height, self.frame.width)),
                                    metadata={'counter': count,
                                              'timestamp': self.frame.timestamp*1e-7})
                count += 1
                
        finally:
            self.camera.runFeatureCommand("AcquisitionStop")
            self.camera.endCapture()
            self.camera.revokeAllFrames()
    
if __name__ == '__main__':
    list = AVT_Camera.get_camera_list()
    for l in list:
        print(l.decode('ascii'))
    
    with AVT_Camera(0) as cam:
        # features
        for f in cam.camera_features():
            print(f)

        print('-'*8)
        
            
        img = cam.acquisition_oneshot()
        
        for feat in ['PixelFormat', 'AcquisitionFrameRate', 'AcquisitionMode',
                     'ExposureAuto', 'ExposureMode', 'ExposureTime',
                     'IIDCMode', 'TriggerMode',
                     'TriggerSource', 'TriggerDelay', ]:
            featDict = cam.camera_feature_info(feat)
            for k, v in featDict.items():
                print(k, ':', v)
            print('-'*8)
        
        
    import matplotlib.pyplot as plt
    plt.imshow(img, origin='lower', cmap='gray')
    plt.show()
        
        
        
    
    