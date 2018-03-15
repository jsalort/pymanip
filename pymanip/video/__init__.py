"""

Module for camera and video recording:

Depends on :
    - opencv2 (conda install --channel conda-forge opencv)
    - hdf5, pyqtgraph, progressbar2 (normal conda channel)

"""

import os
#import gzip
import numpy as np
try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtGui
    has_qtgraph = True
except ModuleNotFoundError:
    has_qtgraph = False
    print('pyqtgraph is not installed.')
import cv2
import h5py
import time
from progressbar import ProgressBar
import asyncio

def save_image(im, ii, basename, zerofill, file_format,
               compression, compression_level):
    if file_format == 'raw':
        filename = ('{:}-{:0'+str(zerofill)+'d}.li16').format(basename, ii+1)
        im.tofile(filename)
    elif file_format == 'npy':
        filename = ('{:}-{:0'+str(zerofill)+'d}.npy').format(basename, ii+1)
        np.save(filename, im)
    elif file_format == 'npy.gz':
        filename = ('{:}-{:0'+str(zerofill)+'d}.npy.gz').format(basename, ii+1)
        with gzip.open(filename, 'wb') as f:
            np.save(f, im)
    elif file_format in ('hdf', 'hdf5'):
        filename = ('{:}-{:0'+str(zerofill)+'d}.hdf5').format(basename, ii+1)
        with h5py.File(filename, 'w') as f:
            f.attrs['counter'] = im.metadata['counter']
            f.attrs['timestamp'] = im.metadata['timestamp'].timestamp()
            # compression='gzip' trop lent pour 30 fps
            # compression='lzf' presque bon mais un peu lent à 30 fps
            f.create_dataset('image', data=im, compression=compression)
    else:
        filename = ('{:}-{:0'+str(zerofill)+'d}.{:}').format(basename, ii+1, file_format)
        if file_format == 'png':
            params = (cv2.IMWRITE_PNG_COMPRESSION, compression_level)
        else:
            params = None
        cv2.imwrite(filename, im, params)
               
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
            
    def preview(self, backend='cv', slice=None, zoom=0.5):
        if backend == 'cv':
            self.preview_cv(slice, zoom)
        elif backend == 'qt':
            self.preview_qt(slice, zoom)
        else:
            raise RuntimeError('Unknown backend "' + backend + '"')

    async def preview_async_cv(self, slice, zoom, name):
        minimum = None
        maximum = None
        cv2.namedWindow(name)
        try:
            for im in self.acquisition():
                #if minimum is None:
                if True:
                    minimum = np.min(im)
                    maximum = np.max(im)
                    #print('min, max:', minimum, maximum)
                if slice:
                    img = ((2**16-1)//(maximum-minimum))*(im[slice[0]:slice[1],slice[2]:slice[3]]-minimum)
                else:
                    img = ((2**16-1)//(maximum-minimum))*(im-minimum)
                l, c = img.shape
                cv2.imshow(name, 
                    cv2.resize(img, (int(l*zoom), int(c*zoom))))
                k = cv2.waitKey(1)
                if k in (0x1b, ord('s')):
                    break
                await asyncio.sleep(0.001)
        except KeyboardInterrupt:
            pass
        finally: 
            cv2.destroyAllWindows()
            
    def preview_cv(self, slice, zoom):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.preview_async_cv(slice, zoom, name="Preview"))
        loop.close()
        
    def preview_qt(self, slice, zoom, app=None):
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
        QtCore.QTimer.singleShot(10, lambda: self.preview_qt(slice, zoom))
        
        if just_started:
            QtGui.QApplication.instance().exec_()
    
    def acquire_to_files(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.acquire_to_files_async(*args, **kwargs))
        loop.close()
        
    async def acquire_to_files_async(self, num, basename, zerofill=4, 
                         dryrun=False, file_format='png', 
                         compression=None, compression_level=3,
                         verbose=True, delay_save=False,
                         progressbar=True, initialising_cams=None):
        """
        Acquire num images and saves to disk

        - basename, zerofill: filename parameters
        - dryrun = True: acquire but don't actually save [default: False]
        - file_format:
            'raw'    -> li16 (binary little-endian 16 bits integers)
            'npy'    -> numpy npy file
            'npy.gz' -> gzip compressed numpy file
            'hdf5'   -> hdf5, with optional compression [default None]
            'png', 'jpg', 'tif' -> image format with opencv imwrite
                            with optional compression level for PNG
                            [default: 3]
        - compression (optional) for HDF5
        - compression_level (optional) for PNG
        - delay_save: records in RAM and save at this end

        returns: image_counter, frame_datetime as lists

        """
        
        dirname = os.path.dirname(basename)
        if len(dirname):
            try:
                os.makedirs(dirname)
            except FileExistsError:
                pass
        count = []
        dt = []
        if verbose:
            dateformat = '%A %d %B %Y - %X'
            starttime = time.time()
            starttime_str = time.strftime(dateformat, time.localtime(starttime))
            print('Camera acquisition started: ' + starttime_str)
        if progressbar:
            bar = ProgressBar(max_value=num)
        computation_time = 0.0
        images = list()
        ii = 0
        async for im in self.acquisition(num, initialising_cams=initialising_cams):
            if dryrun:
                continue
            if delay_save:
                images.append(im.copy())
            else:
                start_time = time.process_time()
                save_image(im, ii, basename, zerofill, file_format, 
                           compression, compression_level)
                computation_time += time.process_time()-start_time
            if hasattr(im, 'metadata'):
                count.append(im.metadata['counter'])
                dt.append(im.metadata['timestamp'])
            ii+=1
            if progressbar:
                bar.update(ii)
            await asyncio.sleep(0.001)
        if progressbar:
            print("")
        if delay_save and not dryrun:
            print('Acquisition complete. Saving to disk...')
            if progressbar:
                bar = ProgressBar(max_value=num)
            for ii, im in enumerate(images):
                start_time = time.process_time()
                save_image(im, ii, basename, zerofill, file_format, 
                           compression, compression_level)
                computation_time += time.process_time()-start_time
                if progressbar:
                    bar.update(ii+1)
                await asyncio.sleep(0.001)
        if progressbar:
            print("")
        dt = np.array(dt)
        if verbose:
            print('Average saving time per image:', 
                  1000*computation_time/(ii+1), 'ms')
            print('average fps =', 1/np.mean(dt[1:]-dt[:-1]))
        return count, dt
            
            
        
        
