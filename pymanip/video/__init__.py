"""

Module for camera and video recording

"""

import numpy as np
try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtGui
    has_qtgraph = True
except ModuleNotFoundError:
    has_qtgraph = False
    print('pyqtgraph is not installed.')

class MetadataArray(np.ndarray):
    """ Array with metadata. """
    
    def __new__(cls, input_array, metadata=None):
        obj = np.asarray(input_array).view(cls)
        obj.metadata = metadata
        return obj
    
    def __array_finalize__(self, obj):
        if obj is None: return
        self.metadata = getattr(obj, 'metadata', None)

class Camera:
    """
    Subclasses must implement:
        - acquisition_oneshot method
        - acquisition generator
        - resolution, name properties
    """
    
    def __enter__(self):
        return self
        
    def __exit__(self, type_, value, cb):
        if hasattr(self, 'preview_generator'):
            self.preview_generator = None
            
    def preview(self, app=None):
        if app:
            self.app = app
            just_started = False
        elif not hasattr(self, 'app'):
            self.app = QtGui.QApplication([])
            just_started = True
        else:
            just_started = False
            
        # create window if it does not already exists
        if not hasattr(self, 'window'):
            self.window = QtGui.QMainWindow()
            self.window.show()
            #self.window.resize(*self.resolution)
            self.window.resize(800,600)
            self.window.setWindowTitle(self.name)
            self.image_view = pg.ImageView()
            self.window.setCentralWidget(self.image_view)
            just_created = True
        else:
            just_created = False
        
        # instantiate generator
        if not hasattr(self, 'preview_generator'):
            self.preview_generator = self.acquisition()
        
        # update view with latest image
        self.image_view.setImage(next(self.preview_generator).T,
                                 autoRange=False, autoLevels=False,
                                 autoHistogramRange=False)
        if just_created:
            self.image_view.autoRange()
            self.image_view.autoLevels()
                                 
        # set timer for refreshing in 10 ms
        QtCore.QTimer.singleShot(10, self.preview)
        
        if just_started:
            QtGui.QApplication.instance().exec_()
            
    def acquire_to_files(self, num, basename):
        """
        Acquire num images and saves PNG to disk
        """
        
        
        