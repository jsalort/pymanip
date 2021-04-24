"""Video acquisition module (:mod:`pymanip.video`)
==================================================

This module defines the :class:`~pymanip.video.Camera` abstract base class,
which implements common methods such as the live video preview, and higher
level simple methods to quickly set up a video recording. It also
defines common useful functions, and a simple extension of Numpy arrays to
hold metadata (such as frame timestamp).

.. autoclass:: Camera
   :members:
   :private-members:

.. autoclass:: CameraTimeout

.. autoclass:: MetadataArray
   :members:
   :private-members:
   :show-inheritance:

   .. attribute:: metadata

      dictionnary attribute containing user-defined key-value pairs

.. autofunction:: save_image

"""

import sys
import signal
import os
import gzip
import numpy as np 

try:
    import pyqtgraph as pg
    from pyqtgraph.Qt import QtCore, QtGui
    from PyQt5.QtWidgets import (
        QMainWindow,
        QWidget,
        QPushButton,
        QVBoxLayout,
        QHBoxLayout,
        QApplication,
        QLabel,
    )

    has_qtgraph = True
except ModuleNotFoundError:
    has_qtgraph = False
    print("pyqtgraph is not installed.")
import cv2
import h5py
import time
from progressbar import ProgressBar
import asyncio
from pymanip.asynctools import synchronize_function, synchronize_generator


class CameraTimeout(Exception):
    """This class defines a CameraTimeout exception.
    """

    pass


def save_image(im, ii, basename, zerofill, file_format, compression, compression_level,
               color_order=None):
    """This function is a simple general function to save an input image from the camera
    to disk.

    :param im: input image
    :type im: :class:`~pymanip.video.MetadataArray`
    :param ii: frame number
    :type ii: int
    :param basename: file basename
    :type basename: str
    :param zerofill: number of digits for the frame number
    :type zerofill: int
    :param file_format: image file format on disk. Possible values are: "raw", "npy", "npy.gz", "hdf5", "png", or a file extension that OpenCV imwrite supports
    :type file_format: str
    :param compression: the compression argument "gzip" or "lzf" to pass to :meth:`h5py.create_dataset` if file_format is "hdf5"
    :type compression: str
    :param compression_level: the png compression level passed to opencv for the "png" file format
    :type compression_level: int

    """
    if file_format == "raw":
        filename = ("{:}-{:0" + str(zerofill) + "d}.li16").format(basename, ii + 1)
        im.tofile(filename)
    elif file_format == "npy":
        filename = ("{:}-{:0" + str(zerofill) + "d}.npy").format(basename, ii + 1)
        np.save(filename, im)
    elif file_format == "npy.gz":
        filename = ("{:}-{:0" + str(zerofill) + "d}.npy.gz").format(basename, ii + 1)
        with gzip.open(filename, "wb") as f:
            np.save(f, im)
    elif file_format in ("hdf", "hdf5"):
        filename = ("{:}-{:0" + str(zerofill) + "d}.hdf5").format(basename, ii + 1)
        with h5py.File(filename, "w") as f:
            f.attrs["counter"] = im.metadata["counter"]
            f.attrs["timestamp"] = im.metadata["timestamp"].timestamp()
            if color_order is not None:
                f.attrs["color_order"] = color_order
            # compression='gzip' trop lent pour 30 fps
            # compression='lzf' presque bon mais un peu lent à 30 fps
            f.create_dataset("image", data=im, compression=compression)
    else:
        filename = ("{:}-{:0" + str(zerofill) + "d}.{:}").format(
            basename, ii + 1, file_format
        )
        if file_format == "png":
            params = (cv2.IMWRITE_PNG_COMPRESSION, compression_level)
        else:
            params = None
        if color_order == "RGB":
            im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)
        cv2.imwrite(filename, im, params)


class MetadataArray(np.ndarray):
    """This class extends Numpy array to allow for an additionnal metadata
    attribute.
    """

    def __new__(cls, input_array, metadata=None):
        obj = np.asarray(input_array).view(cls)
        obj.metadata = metadata
        return obj

    def __array_finalize__(self, obj):
        if obj is None:
            return
        self.metadata = getattr(obj, "metadata", None)


class Camera:
    """This class is the abstract base class for all other concrete camera classes.
    The concrete sub-classes *must* implement the following methods:

    - :meth:`acquisition_oneshot` method

    - :meth:`acquisition` and :meth:`acquisition_async` generator methods

    - :attr:`resolution`, :attr:`name` and :attr:`bitdepth` properties

    The concrete sub-classes will also probably have to override the constructor
    method, and the enter/exit context manager method, as well as common property getters
    and setters:

    - :meth:`set_exposure_time`

    - :meth:`set_trigger_mode`

    - :meth:`set_roi`

    - :meth:`set_frame_rate`

    It may also define specialized getters for the camera which support them:

    - :meth:`set_adc_operating_mode`: ADC operating mode

    - :meth:`set_pixel_rate`: pixel rate sensor readout (in Hz)

    - :meth:`set_delay_exposuretime`

    """

    def acquisition_oneshot(self):
        """This method must be implemented in the sub-classes.
        It starts the camera, grab one frame, stops the camera, and returns the frame. It is useful for testing
        purposes, or in cases where only one frame is desired between very long time delays. It takes no input parameters.
        Returns an "autonomous" array (the buffer is independant of the camera object).

        :return: frame
        :rtype: :class:`~pymanip.video.MetadataArray`

        """
        raise NotImplementedError()

    def acquisition(
        self,
        num=np.inf,
        timeout=1000,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
    ):
        """This generator method is the main method that sub-classes must implement, along with the asynchronous variant.
        It is used by all the other higher-level methods, and can also be used directly in user code.

        :param num: number of frames to acquire, defaults to float("inf").
        :type num: int, or float("inf"), optional
        :param timout: timeout for frame acquisition (in milliseconds)
        :type timeout: int, optional
        :param raw: if True, returns bytes from the camera without any conversion. Defaults to False.
        :type raw: bool, optional
        :param initialising_cams: None, or set of camera objects. This camera object will remove itself from this set, once it is ready to grab frames. Useful in the case of multi camera acquisitions, to determine when all cameras are ready to grab frames. Defaults to None.
        :type initialising_cams: set, optional
        :param raise_on_timeout: boolean indicating whether to actually raise an exception when timeout occurs
        :type raise_on_timeout: bool, optional

        It starts the camera, yields :obj:`num` images, and closes the camera.
        It can be aborted when sent a true-truth value object. It then cleanly
        stops the camera and finally yields True as a confirmation that the stop_signal has been caught before returning.
        Sub-classes must therefore reads the possible stop_signal when yielding the frame, and act accordingly.

        The :class:`~pymanip.video.MetadataArray` objects yielded by this generator use a shared memory buffer which may
        be overriden for the next frame, and which is no longer defined when the generator object is cleaned up.
        The users are responsible for copying the array, if they want a persistant copy.

        User-level code will use the generator in this manner:

        .. code-block:: python

            gen = cam.acquire()
            for frame in gen:

                # .. do something with frame ..

                if I_want_to_stop:
                    clean = gen.send(True)
                    if not clean:
                        print('Warning generator not cleaned')
                    # no need to break here because the gen will be automatically exhausted

        """
        yield from synchronize_generator(
            self.acquisition_async, num, timeout, raw, None, raise_on_timeout
        )

    async def acquisition_async(
        self,
        num=np.inf,
        timeout=1000,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
    ):
        """This asynchronous generator method is similar to the :meth:`~pymanip.video.Camera.acquisition` generator method,
        except asynchronous. So much so, that in the general case, the latter can be defined simply by yielding from this
        asynchronous generator (so that the code is written once for both use cases), i.e.

        .. code-block:: python

            from pymanip.asynctools import synchronize_generator

            def acquisition(
                self,
                num=np.inf,
                timeout=1000,
                raw=False,
                initialising_cams=None,
                raise_on_timeout=True,
            ):
                yield from synchronize_generator(
                    self.acquisition_async,
                    num,
                    timeout,
                    raw,
                    initialising_cams,
                    raise_on_timeout,
                )

        It starts the camera, yields :obj:`num` images, and closes the camera.
        It can stop yielding images by sending the generator object a true-truth value object. It then cleanly
        stops the camera and finally yields True as a confirmation that the stop_signal has been caught before returning.
        Sub-classes must therefore reads the possible stop_signal when yielding the frame, and act accordingly.

        The :class:`~pymanip.video.MetadataArray` objects yielded by this generator use a shared memory buffer which may
        be overriden for the next frame, and which is no longer defined when the generator object is cleaned up.
        The users are responsible for copying the array, if they want a persistant copy.

        The user API is similar, except with asynchronous calls, i.e.

        .. code-block:: python

            gen = cam.acquire_async()
            async for frame in gen:

                # .. do something with frame ..

                if I_want_to_stop:
                    clean = await gen.asend(True)
                    if not clean:
                        print('Warning generator not cleaned')
                    # no need to break here because the gen will be automatically exhausted


        """
        raise NotImplementedError()

    def __enter__(self):
        """Context manager enter method
        """
        return self

    def __exit__(self, type_, value, cb):
        """Context manager exit method
        """
        if hasattr(self, "preview_generator"):
            self.preview_generator = None

    def preview(self, backend="cv", slice_=None, zoom=0.5, rotate=0):
        """This methods starts and synchronously runs the live-preview GUI.

        :param backend: GUI library to use. Possible values: "cv" for OpenCV GUI, "qt" for PyQtGraph GUI.
        :type backend: str
        :param slice_: coordinate of the region of interest to show, defaults to None
        :type slice_: Iterable[int], optional
        :param zoom: zoom factor, defaults to 0.5
        :type zoom: float, optional
        :param rotate: image rotation angle, defaults to 0
        :type rotate: float, optional

        """

        if backend == "cv":
            self.preview_cv(slice_, zoom, rotate)
        elif backend == "qt":
            self.preview_qt(slice_, zoom, None, rotate)
        else:
            raise RuntimeError('Unknown backend "' + backend + '"')

    async def preview_async_cv(self, slice_, zoom, name, rotate=0):
        """This method starts and asynchronously runs the live-preview with OpenCV GUI.
        The params are identical to the :meth:`~pymanip.video.Camera.preview` method.
        """

        minimum = None
        maximum = None
        cv2.namedWindow(name)
        try:
            preview_generator = self.acquisition_async()
            async for im in preview_generator:
                # if minimum is None:
                if True:
                    minimum = np.min(im)
                    maximum = np.max(im)
                    # print('min, max:', minimum, maximum)
                maxint = np.iinfo(im.dtype).max
                if rotate == 90.0:
                    im = cv2.rotate(im, cv2.ROTATE_90_COUNTERCLOCKWISE)
                elif rotate == -90.0:
                    im = cv2.rotate(im, cv2.ROTATE_90_CLOCKWISE)
                try:
                    l, c = im.shape
                    color = False
                except ValueError:
                    l, c, ncomp = im.shape
                    color = True

                if slice_:
                    if color:
                        img = (maxint // (maximum - minimum)) * (
                            im[slice_[0] : slice_[1], slice_[2] : slice_[3], :] - minimum
                        )
                    else:
                        img = (maxint // (maximum - minimum)) * (
                            im[slice_[0] : slice_[1], slice_[2] : slice_[3]] - minimum
                        )

                else:
                    img = (maxint // (maximum - minimum)) * (im - minimum)
                img = cv2.resize(img, (int(c * zoom), int(l * zoom)))
                if color and self.color_order == "RGB":
                    # OpenCV works in BGR order.
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                cv2.imshow(name, img)
                k = cv2.waitKey(1)
                if k in (0x1B, ord("s")):
                    clean = await preview_generator.asend(True)
                    if not clean:
                        print("Generator not cleaned")
                    break
                await asyncio.sleep(0.001)
        except KeyboardInterrupt:
            pass
        finally:
            cv2.destroyAllWindows()

    def preview_cv(self, slice_, zoom, rotate=0):
        """This method starts and synchronously runs the live-preview with OpenCV GUI.
        It is a wrapper around the :meth:`pymanip.video.Camera.preview_async_cv` method.
        The params are identical to the :meth:`~pymanip.video.Camera.preview` method.
        """
        return synchronize_function(
            self.preview_async_cv, slice_, zoom, name="Preview", rotate=rotate
        )

    def preview_exitHandler(self):
        """This method sends a stop signal to the camera acquisition generator of the
        live-preview GUI.
        """

        clean = self.preview_generator.send(True)
        if not clean:
            print("Generator not cleaned")

    def display_crosshair(self):
        """This method adds a centered crosshair for self-reflection to the live-preview
        window (qt backend only)
        """
        if self.crosshair_chkbox.isChecked():
            self.vLine = pg.InfiniteLine(
                pos=(self.camera.Width / 2, 0), angle=90, movable=False
            )
            self.hLine = pg.InfiniteLine(
                pos=(0, self.camera.Height / 2), angle=0, movable=False
            )
            self.image_view.addItem(self.vLine, ignoreBounds=True)
            self.image_view.addItem(self.hLine, ignoreBounds=True)
        else:
            self.image_view.removeItem(self.vLine)
            self.image_view.removeItem(self.hLine)

    def preview_qt(self, slice, zoom, app=None, rotate=0):
        """This methods starts and synchronously runs the live-preview with Qt GUI.
        The params are identical to the :meth:`~pymanip.video.Camera.preview` method.
        """
        if app:
            self.app = app
            just_started = False
        elif not hasattr(self, "app"):
            self.app = QtGui.QApplication([])
            self.app.aboutToQuit.connect(self.preview_exitHandler)
            just_started = True
        else:
            just_started = False

        # create window if it does not already exists
        if not hasattr(self, "window"):
            self.window = QtGui.QMainWindow()
            # self.window.resize(*self.resolution)
            self.window.resize(800, 600)
            self.window.setWindowTitle(self.name)
            self.image_view = pg.ImageView()
            self.window.setCentralWidget(self.image_view)
            self.range_set = False

            # adding widget for controlling the background subtraction
            # and a crosshair overlay
            self.central_widget = QWidget()
            self.tools_widget = QWidget()
            self.central_layout = QVBoxLayout(self.central_widget)
            self.tools_layout = QHBoxLayout(self.tools_widget)

            self.crosshair_chkbox = QtGui.QCheckBox("Crosshair", self.tools_widget)
            self.subtraction_chkbox = QtGui.QCheckBox(
                "Background subtraction", self.tools_widget
            )
            self.learning_label = QLabel(
                "Learning rate  [0, 1] :", parent=self.tools_widget
            )
            self.spnbx_learning = QtGui.QDoubleSpinBox(
                parent=self.tools_widget, value=0.05
            )
            self.spnbx_learning.setRange(0, 1)
            self.spnbx_learning.setSingleStep(0.01)
            self.spnbx_learning.setDecimals(3)
            self.acq_btn = QtGui.QPushButton("Acquisition", self.tools_widget)
            self.exposure_label = QLabel(
                "Exposure time (s) :", parent=self.tools_widget
            )
            self.spnbox_exposure = QtGui.QDoubleSpinBox(
                parent=self.tools_widget, value=0.001
            )
            self.spnbox_exposure.setRange(0.000033, 67.108895)
            self.spnbox_exposure.setSingleStep(0.0001)
            self.spnbox_exposure.setDecimals(4)

            self.tools_layout.addWidget(self.crosshair_chkbox)
            self.tools_layout.addWidget(self.subtraction_chkbox)
            self.tools_layout.addWidget(self.learning_label)
            self.tools_layout.addWidget(self.spnbx_learning)
            self.tools_layout.addWidget(self.exposure_label)
            self.tools_layout.addWidget(self.spnbox_exposure)
            self.tools_layout.addWidget(self.acq_btn)

            self.central_layout.addWidget(self.image_view)
            self.central_layout.addWidget(self.tools_widget)

            self.window.setCentralWidget(self.central_widget)

            self.crosshair_chkbox.stateChanged.connect(self.display_crosshair)

            # hide useless buttons
            self.image_view.ui.roiBtn.hide()
            self.image_view.ui.menuBtn.hide()

            self.window.show()

        # instantiate generator
        if not hasattr(self, "preview_generator"):
            self.preview_generator = self.acquisition(timeout=1000, raise_on_timeout=False)

        if just_started:
            self.bkgrd = None

        # update view with latest image if it is ready
        # do nothing otherwise (to allow GUI interaction while waiting
        # for camera reading)
        img = next(self.preview_generator)
        if img is not None:
            try:
                l, c = img.shape
                color = False
            except ValueError:
                l, c, ncomp = img.shape
                color = True
            if zoom != 1.0:
                img = cv2.resize(img, (int(c * zoom), int(l * zoom)))
            if rotate == 90.0:
                img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif rotate == -90.0:
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)

            if self.subtraction_chkbox.isChecked():
                if self.bkgrd is None:
                    self.bkgrd = img
                    self.range_set = False
                learning_rate = self.spnbx_learning.value()
                self.bkgrd = (1 - learning_rate) * self.bkgrd + learning_rate * img

                self.bkgrd = self.bkgrd.astype(np.int32)
                img = img - self.bkgrd  # self.bkgrd - img
                img[img < 0] = 0
                img = img.astype(np.uint16)
            if not color:
                img = img.T
            else:
                img = np.transpose(img, axes=(1,0,2))
                if self.color_order == "BGR":
                    # Qt comme Matplotlib travaille en RGB.
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            self.image_view.setImage(
                img, autoRange=False, autoLevels=False, autoHistogramRange=False
            )
            if not self.range_set:
                self.image_view.autoRange()
                self.image_view.autoLevels()
                self.range_set = True

        # set timer for refreshing in 10 ms
        QtCore.QTimer.singleShot(
            10, lambda: self.preview_qt(slice, zoom, self.app, rotate)
        )

        if just_started:
            QtGui.QApplication.instance().exec_()

    def acquire_to_files(self, *args, **kwargs):
        """This method starts the camera, acquires images and saves them to the disk.
        It is a simple wrapper around the :meth:`pymanip.video.Camera.acquire_to_files_async` asynchronous
        method. The parameters are identical.
        """
        return synchronize_function(self.acquire_to_files_async, *args, **kwargs)

    def acquire_signalHandler(self, *args, **kwargs):
        """This method sends a stop signal to the :meth:`~pymanip.video.Camera.acquire_to_files_async` method.
        """
        self.acqinterrupted = True

    async def acquire_to_files_async(
        self,
        num,
        basename,
        zerofill=4,
        dryrun=False,
        file_format="png",
        compression=None,
        compression_level=3,
        verbose=True,
        delay_save=False,
        progressbar=True,
        initialising_cams=None,
        **kwargs
    ):
        """This asynchronous method starts the camera, acquires :obj:`num` images and saves them to the disk. It is
        a simple quick way to perform camera acquisition (one-liner in the user code).

        :param num: number of frames to acquire
        :type num: int
        :param basename: basename for image filenames to be saved on disk
        :type basename: str
        :param zerofill: number of digits for the framenumber for image filename, defaults to 4
        :type zerofill: int, optional
        :param dryrun: do the acquisition, but saves nothing (testing purposes), defaults to False
        :type dryrun: bool, optional
        :param file_format: format for the image files, defaults to "png". Possible values are "raw", "npy", "npy.gz", "hdf5", "png" or any other extension supported by OpenCV imwrite.
        :type file_format: str, optional
        :param compression: compression option for HDF5 format ("gzip", "lzf"), defaults to None.
        :type compression: str, optional
        :param compression_level: png compression level for PNG format, defaults to 3.
        :type compression_level: int, optional
        :param verbose: prints information message, defaults to True.
        :type verbose: bool, optional
        :param delay_save: records all the frame in RAM, and saves at the end. This is useful for fast framerates when saving time is too slow. Defaults to False.
        :type delay_save: bool, optional
        :param progressbar: use :mod:`progressbar` module to show a progress bar. Defaults to True.
        :type progressbar: bool, optional
        :param initialising_cams: None, or set of camera objects. This camera object will remove itself from this set, once it is ready to grab frames. Useful in the case of multi camera acquisitions, to determine when all cameras are ready to grab frames. Defaults to None.
        :type initialising_cams: set, optional
        :return: image_counter, frame_datetime
        :rtype: list, list

        The details of the file format are given in this table:

        ===============     ========================================================================
        file_format         description
        ===============     ========================================================================
        raw                 native 16 bits integers, i.e. li16 (little-endian) on Intel CPUs
        npy                 numpy npy file (warning: depends on pickle format)
        npy.gz              gzip compressed numpy file
        hdf5                hdf5, with optional compression
        png, jpg, tif       image format with opencv imwrite with optional compression level for PNG
        ===============     ========================================================================

        Typical usage of the function for one camera:

        .. code-block:: python

            async def main():

                with Camera() as cam:
                    counts, times = await cam.acquire_to_files_async(num=20, basename='img-')

            asyncio.run(main())


        """

        # signal handling
        if sys.platform == "win32":
            signal.signal(signal.SIGINT, self.acquire_signalHandler)
        else:
            loop = asyncio.get_event_loop()
            for signame in ("SIGINT", "SIGTERM"):
                loop.add_signal_handler(
                    getattr(signal, signame), self.acquire_signalHandler
                )

        dirname = os.path.dirname(basename)
        if len(dirname):
            try:
                os.makedirs(dirname)
            except FileExistsError:
                pass
        count = []
        dt = []
        if verbose:
            dateformat = "%A %d %B %Y - %X"
            starttime = time.time()
            starttime_str = time.strftime(dateformat, time.localtime(starttime))
            print("Camera acquisition started: " + starttime_str)
        if progressbar:
            bar = ProgressBar(max_value=num)
        computation_time = 0.0
        images = list()
        ii = 0
        acqgen = self.acquisition_async(
            num, initialising_cams=initialising_cams, **kwargs
        )
        self.acqinterrupted = False
        async for im in acqgen:
            if ii == 0:
                print(im.dtype)
            if not dryrun:
                if delay_save:
                    images.append(im.copy())
                else:
                    start_time = time.process_time()
                    if hasattr(self, "color_order"):
                        color_order = self.color_order
                    else:
                        color_order = None
                    if im.ndim < 3:
                        color_order = None
                    save_image(
                        im,
                        ii,
                        basename,
                        zerofill,
                        file_format,
                        compression,
                        compression_level,
                        color_order=color_order,
                    )
                    computation_time += time.process_time() - start_time
            if hasattr(im, "metadata"):
                count.append(im.metadata["counter"])
                ts = im.metadata["timestamp"]
                try:
                    ts = ts.timestamp()
                except AttributeError:
                    pass
                dt.append(ts)
            ii += 1
            if progressbar:
                try:
                    bar.update(ii)
                except Exception:
                    print(ii)
            await asyncio.sleep(0.001)
            if self.acqinterrupted:
                print("")
                print("Signal caught... Stopping camera acquisition...")
                clean = await acqgen.asend(True)
                if not clean:
                    print("Camera was not successfully interrupted")
                break
        if progressbar:
            print("")
        if delay_save and not dryrun:
            print("Acquisition complete. Saving to disk...")
            if progressbar:
                bar = ProgressBar(max_value=ii)
            for ii, im in enumerate(images):
                start_time = time.process_time()
                save_image(
                    im,
                    ii,
                    basename,
                    zerofill,
                    file_format,
                    compression,
                    compression_level,
                )
                computation_time += time.process_time() - start_time
                if progressbar:
                    try:
                        bar.update(ii + 1)
                    except Exception:
                        print(ii)
                await asyncio.sleep(0.0001)
        if progressbar:
            print("")
        dt = np.array(dt)
        if verbose:
            print(
                "Average saving time per image:",
                1000 * computation_time / (ii + 1),
                "ms",
            )
            print("average fps =", 1 / np.mean(dt[1:] - dt[:-1]))
            if images:
                print("image size:", images[0].shape)
                print("image dtype:", images[0].dtype)
        return count, dt
