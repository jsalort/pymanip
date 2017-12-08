import numpy as np
from pymanip.video import MetadataArray, Camera
from pymba import Vimba

class AVT_Camera(Camera):
    # Class attributes
    system = None
    vimba = None
    active_cameras = []
    
    @classmethod
    def get_camera_list(cls):
        if cls.vimba:
            return cls.vimba.getCameraIds()
        else:
            with Vimba() as vimba_:
                return vimba_.getCameraIds()
        
    def __init__(self, cam_num):
        if not AVT_Camera.vimba:
            AVT_Camera.vimba = Vimba().__enter__()
        if not AVT_Camera.system:
            AVT_Camera.system = AVT_Camera.vimba.getSystem()
        self.cameraDesc = AVT_Camera.get_camera_list()[cam_num]
        #self.info = vimba.getCameraInfo(self.cameraDesc)
        self.camera = AVT_Camera.vimba.getCamera(self.cameraDesc)
        self.camera.openCamera()
        AVT_Camera.active_cameras.append(self)
    
    def close(self):
        self.camera.closeCamera()
        self.camera = None
        AVT_Camera.active_cameras.pop(self)
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
        self.frame = self.camera.getFrame()
        self.frame.announceFrame()
        self.camera.startCapture()
        try:
            self.frame.queueFrameCapture()
            self.camera.runFeatureCommand('AcquisitionStart')
            self.camera.runFeatureCommand('AcquisitionStop')
            self.frame.waitFrameCapture()
            print(dir(self.frame))
            print('timestamp =', self.frame.timestamp)
            print('pixel_bytes =', self.frame.pixel_bytes)
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
        
    def acquisition(self, num=np.inf, timeout=1000, raw=False):
        """
        Multiple image acquisition
        yields a shared memory numpy array valid only
        before generator object cleanup.
        """
        
        
        
if __name__ == '__main__':
    list = AVT_Camera.get_camera_list()
    for l in list:
        print(l.decode('ascii'))
    
    #with AVT_Camera(0) as cam:
    cam = AVT_Camera(0)
    cam.__enter__()
    if True:
        # features
        for f in cam.camera_features():
            print(f)

        print('-'*8)
        
            
        img = cam.acquisition_oneshot()
        
        for feat in ['PixelFormat', 'SensorBits']:
            featDict = cam.camera_feature_info(feat)
            for k, v in featDict.items():
                print(k, ':', v)
            print('-'*8)
        
        
    import matplotlib.pyplot as plt
    plt.imshow(img, origin='lower', cmap='gray')
    plt.show()
        
        
        
    
    