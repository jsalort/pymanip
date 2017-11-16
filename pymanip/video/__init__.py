"""

Module for camera and video recording

"""

#import gzip
import numpy as np
try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtGui
    has_qtgraph = True
except ModuleNotFoundError:
    has_qtgraph = False
    print('pyqtgraph is not installed.')
from . import png
import h5py

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
        - resolution, name, bitdepth properties
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
            
    def acquire_to_files(self, num, basename, zerofill=4, dryrun=False, 
                         raw=True, compression=None):
        """
        Acquire num images and saves PNG to disk
        """
        
        writer = None
        count = []
        dt = []
        for ii, im in enumerate(self.acquisition(num)):
            if raw:
                # brut de chez brut
                #filename = ('{:}-{:0'+str(zerofill)+'d}.li16').format(basename, ii+1)
                #im.tofile(filename)
                # version npy simple
                #filename = ('{:}-{:0'+str(zerofill)+'d}.npy').format(basename, ii+1)
                #np.save(filename, im)
                # version npy compressé (lent)
                #filename = ('{:}-{:0'+str(zerofill)+'d}.npy.gz').format(basename, ii+1)
                #with gzip.open(filename, 'wb') as f:
                #    np.save(f, im)
                filename = ('{:}-{:0'+str(zerofill)+'d}.hdf5').format(basename, ii+1)
                with h5py.File(filename, 'w') as f:
                    f.attrs['counter'] = im.metadata['counter']
                    f.attrs['timestamp'] = im.metadata['timestamp'].timestamp()
                    # compression='gzip' trop lent pour 30 fps
                    # compression='lzf' presque bon mais un peu lent à 30 fps
                    f.create_dataset('image', data=im, compression=compression)
                count.append(im.metadata['counter'])
                dt.append(im.metadata['timestamp'])
            else:
                if not writer:
                    row_count, column_count = im.shape
                    writer = png.Writer(column_count, row_count, greyscale=True,
                                        alpha=False, bitdepth=self.bitdepth)
                filename = ('{:}-{:0'+str(zerofill)+'d}.png').format(basename, ii+1)
                if not dryrun:
                    with open(filename, 'wb') as f:
                        writer.write(f, im)
                if hasattr(im, 'metadata'):
                    count.append(im.metadata['counter'])
                    dt.append(im.metadata['timestamp'])
        return count, dt
            
            
        
        