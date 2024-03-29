"""Ximea Camera module (:mod:`pymanip.video.ximea.camera`)
==========================================================

This module implements the :class:`pymanip.video.ximea.Ximea_Camera` using the
`Python module provided by Ximea <https://www.ximea.com/support/wiki/apis/Python_inst_win>`_.

.. autoclass:: Ximea_Camera
   :members:
   :private-members:
   :show-inheritance:

"""

from pathlib import Path
import asyncio
import ctypes
import ctypes.wintypes as wintypes

import numpy as np
from pymanip.video import MetadataArray, Camera, CameraTimeout

from ximea import xiapi
from ximea.xidefs import XI_IMG_FORMAT, XI_TRG_SOURCE, XI_TRG_SELECTOR, XI_IMG, XI_COLOR_FILTER_ARRAY

ximea_base = Path(r"C:\XIMEA")
xiapi_dng_store_dll = ximea_base / "DNG Store" / "binX64" / "xiapi_dng_store.dll"
if xiapi_dng_store_dll.exists():
    xiapi_dng_store = ctypes.CDLL(str(xiapi_dng_store_dll))
else:
    print("DNG Store DLL not found. DNG will not be available.")

XI_RETURN = ctypes.c_int

class XI_DNG_METADATA(ctypes.Structure):
    _fields_ = [
        # required parameters
        ("cfa", ctypes.c_int),  # bayer matrix type
        ("maxPixelValue", ctypes.c_int),  # maximum pixel value, important for 16-bit image formats (i.e. 255 for 8-bit formats)
        # optional parameters
        ("cameraModelName", ctypes.c_char * 256),  # camera model name, encoded in UTF8
        ("cameraSerialNumber", ctypes.c_char * 256),
        ("cameraUserId", ctypes.c_char * 256),  # camera ID given by the user, encoded in UTF8
        ("autoExposureOn", ctypes.c_int),  # 1: on, 0: off, -1: N/A
        ("autoWhiteBalanceOn", ctypes.c_int),  # 1: on, 0: off, -1: N/A
        ("whiteBalanceR", ctypes.c_float),  # white balance coefficients
        ("whiteBalanceG", ctypes.c_float),
        ("whiteBalanceB", ctypes.c_float),
        ("lensAperture", ctypes.c_float),
        ("lensFocalLength", ctypes.c_float),
        ("acqTimeYear", ctypes.c_int),
        ("acqTimeMonth", ctypes.c_int),
        ("acqTimeDay", ctypes.c_int),
        ("acqTimeHour", ctypes.c_int),
        ("acqTimeMinute", ctypes.c_int),
        ("acqTimeSecond", ctypes.c_int),
    ]
    
    def as_dict(self):
        for bayer_matrix_name, value in XI_COLOR_FILTER_ARRAY.items():
            if value == self.cfa:
                break
        else:
            bayer_matrix_name = f"Unknown ({value:})"
        return {
            "cfa": bayer_matrix_name,
            "maxPixelValue": self.maxPixelValue,
            "cameraModelName": self.cameraModelName,
            "cameraSerialNumber": self.cameraSerialNumber,
            "cameraUserId": self.cameraUserId,
            "autoExposureOn": {1: True, -1: False}.get(self.autoExposureOn, None),
            "autoWhiteBalanceOn": {1: True, -1: False}.get(self.autoWhiteBalanceOn, None),
            "whiteBalanceR": self.whiteBalanceR,
            "whiteBalanceG": self.whiteBalanceG,
            "whiteBalanceB": self.whiteBalanceB,
            "lensAperture": self.lensAperture,
            "acqTimeYear": self.acqTimeYear,
            "acqTimeMonth": self.acqTimeMonth,
            "acqTimeDay": self.acqTimeDay,
            "acqTimeHour": self.acqTimeHour,
            "acqTimeMinute": self.acqTimeMinute,
            "acqTimeSecond": self.acqTimeSecond,
        }

class Ximea_Camera(Camera):
    """Concrete :class:`pymanip.video.Camera` class for Ximea camera.
    """

    def __init__(self, serial_number=None, pixelFormat=None):
        """Constructor method
        """
        # pour le moment on ouvre simplement la première caméra
        self.cam = xiapi.Camera()
        if serial_number is None:
            self.cam.open_device()
        else:
            self.cam.open_device_by_SN(serial_number)
        if pixelFormat is None:
            if self.cam.is_iscolor():
                pixelFormat = "XI_RGB24"
            else:
                pixelFormat = "XI_MONO8"
        elif pixelFormat not in XI_IMG_FORMAT:
            raise ValueError(
                f"Wrong pixelFormat. Possible values are {set(XI_IMG_FORMAT.keys()):}"
            )
        self.cam.set_imgdataformat(pixelFormat)
        self.pixelFormat = pixelFormat
        if self.cam.is_iscolor():
            if pixelFormat in ("XI_RGB24", ):
                self.color_order = "BGR"  # Ximea RGB mode is [blue][green][red] per the doc.
            elif pixelFormat in ("XI_RAW8", "XI_RAW16"):
                cfa = self.cam.get_cfa()
                assert cfa == "XI_CFA_BAYER_GBRG"
                self.color_order = "BayerGR"
            else:
                self.color_order = None
        else:
            self.color_order = None
        print(f"Camera {self.name:} opened ({pixelFormat:})")

    def close(self):
        """Close connection to the camera
        """
        name = self.name
        self.cam.close_device()
        self.cam = None
        print(f"Connection to camera {name:} closed.")

    def __exit__(self, type_, value, cb):
        """Context manager exit method
        """
        super().__exit__(type_, value, cb)
        self.close()

    @property
    def name(self):
        """Camera name
        """
        return self.cam.get_device_name().decode("ascii")

    def set_exposure_time(self, seconds):
        """This method sets the exposure time for the camera.

        :param seconds: exposure in seconds.
        :type seconds: float
        """
        self.cam.set_exposure(int(seconds * 1e6))
        print("Exposure time set to", 1000 * seconds, "ms")

    def get_exposure_time(self):
        """This method gets the exposure time in seconds for the camera.
        """
        return self.cam.get_exposure() / 1e6

    def set_auto_white_balance(self, toggle):
        """Enable/Disable auto white balance

        :param toggle: True if auto white balance
        :type toggle: bool
        """
        self.cam.set_param("auto_wb", toggle)

    def set_trigger_mode(self, external):
        """Set external trigger (edge rising).
        """
        if external:
            self.cam.set_gpi_mode("XI_GPI_TRIGGER")
            self.cam.set_trigger_source("XI_TRG_EDGE_RISING")
            self.cam.set_trigger_selector("XI_TRG_SEL_EXPOSURE_START")
        else:
            self.cam.set_trigger_source("XI_TRG_OFF")

    def set_vertical_skipping(self, factor):
        """Set vertical skipping
        """
        self.cam.set_downsampling_type("XI_SKIPPING")
        self.cam.set_decimation_vertical(factor)

    def set_limit_bandwidth(self, limit):
        """Enable limit bandwidth (useful if there are several cameras
        acquiring simultaneously).
        """
        if limit:
            self.cam.set_limit_bandwidth_mode("XI_ON")
        else:
            self.cam.set_limit_bandwidth_mode("XI_OFF")

    def get_trigger_mode(self):
        """Returns True if external, False if software
        """
        return self.cam.get_trigger_source() != "XI_TRG_OFF"

    def set_downsampling(self, binning):
        """Change image resolution by binning
        """
        self.cam.set_downsampling(binning)

    def set_roi(self, roiX0=0, roiY0=0, roiX1=0, roiY1=0):
        """This method sets the positions of the upper left corner (X0,Y0) and lower right
        (X1,Y1) corner of the ROI (region of interest) in pixels.
        """
        # Get bounds for width and height (with no offset)
        self.cam.set_offsetX(0)
        self.cam.set_offsetY(0)
        width_increment = self.cam.get_width_increment()
        width_minimum = self.cam.get_width_minimum()
        width_maximum = self.cam.get_width_maximum()
        height_increment = self.cam.get_height_increment()
        height_minimum = self.cam.get_height_minimum()
        height_maximum = self.cam.get_height_maximum()

        # Compute width and height
        width = roiX1 - roiX0
        height = roiY1 - roiY0

        # Check bounds for width and height
        if width < width_minimum:
            print("Minimum width is", width_minimum, "(got", width, ")")
            width = width_minimum
        elif width > width_maximum:
            print("Maximum width is", width_maximum, "(got", width, ")")
            width = width_maximum
        if height < height_minimum:
            print("Minimum height is", height_minimum, "(got", height, ")")
            height = height_minimum
        elif height > height_maximum:
            print("Maximum height is", height_maximum, "(got", height, ")")
            height = height_maximum
        if width % width_increment != 0:
            print("Rounding ROI width with", width_increment, "pixel increments")
            width -= width % width_increment
        if height % height_increment != 0:
            print("Rounding ROI height with", height_increment, "pixel increments")
            height -= height % height_increment

        # Set width and height
        self.cam.set_width(width)
        self.cam.set_height(height)

        # Get bounds for offsets
        offsetX_minimum = self.cam.get_offsetX_minimum()
        offsetX_maximum = self.cam.get_offsetX_maximum()
        offsetX_increment = self.cam.get_offsetX_increment()
        offsetY_minimum = self.cam.get_offsetY_minimum()
        offsetY_maximum = self.cam.get_offsetY_maximum()
        offsetY_increment = self.cam.get_offsetY_increment()

        # Compute offsets
        offset_x = roiX0
        offset_y = roiY0

        # Check bounds for offsets
        if offset_x < offsetX_minimum:
            print("Minimum x-offset is", offsetX_minimum)
            offset_x = offsetX_minimum
        elif offset_x > offsetX_maximum:
            print("Maximum x-offset is", offsetX_maximum)
            offset_x = offsetX_maximum
        if offset_x % offsetX_increment != 0:
            print("Rounding x-offset to", offsetX_increment, "pixel increments")
            offset_x -= offset_x % offsetX_increment
        if offset_y < offsetY_minimum:
            print("Minimum y-offset is", offsetY_minimum)
            offset_y = offsetY_minimum
        elif offset_y > offsetY_maximum:
            print("Maximum y-offset is", offsetY_maximum)
            offset_y = offsetY_maximum
        if offset_y % offsetY_increment != 0:
            print("Rounding y-offset to", offsetY_increment, "pixel increments")
            offset_y -= offset_y % offsetY_increment

        # Set offsets
        self.cam.set_offsetX(offset_x)
        self.cam.set_offsetY(offset_y)

        # Print final ROI
        print("ROI set to", offset_x, offset_y, offset_x + width, offset_y + height)

    def get_roi(self):
        """Get ROI
        """
        width = self.cam.get_width()
        height = self.cam.get_height()
        offset_x = self.cam.get_offsetX()
        offset_y = self.cam.get_offsetY()
        return offset_x, offset_x + width, offset_y, offset_y + height
        
    def set_frame_rate(self, framerate_fps):
        """Sets the framerate in frames per seconds
        """
        self.cam.set_acq_timing_mode("XI_ACQ_TIMING_MODE_FRAME_RATE_LIMIT")
        self.cam.set_framerate(framerate_fps)

    async def get_image(self, loop, image, timeout=5000):
        """Asynchronous version of xiapi.Camera.get_image method
        This function awaits for next image to be available in transport buffer.
        Color images are in BGR order (similar to OpenCV default).
        Attention: matplotlib expects RGB order.

        :param image: Image instance to copy image to
        :type image: :class:`xiapi.Image`
        :param timeout: timeout in milliseconds
        :type timeout: int
        """
        stat = await loop.run_in_executor(
            None,
            self.cam.device.xiGetImage,
            self.cam.handle,
            ctypes.wintypes.DWORD(timeout),
            ctypes.byref(image),
        )

        if stat == 10:
            raise CameraTimeout
        elif stat != 0:
            raise xiapi.Xi_error(stat)

    async def acquisition_async(
        self,
        num=np.inf,
        timeout=None,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
        wait_before_stopping=None,
    ):
        """Concrete implementation of :meth:`pymanip.video.Camera.acquisition_async` for the Ximea camera.

        timeout in milliseconds.
        
        :param raw: if True, returns the XI_IMG object instead of a numpy array.
        :type raw: bool (optional)
        :param wait_before_stopping: async function to be awaited before stopping the acquisition_async
        :type wait_before_stopping: async function (optional)
        
        """
        loop = asyncio.get_event_loop()
        if timeout is None:
            timeout = max((5000, 5 * self.get_exposure_time() * 1000))
        img = xiapi.Image()
        self.cam.start_acquisition()
        try:
            count = 0
            while count < num:
                if (
                    count == 0
                    and initialising_cams is not None
                    and self in initialising_cams
                ):
                    initialising_cams.remove(self)
                try:
                    await self.get_image(loop, img, timeout)
                except CameraTimeout:
                    if raise_on_timeout:
                        raise
                    else:
                        stop_signal = yield None
                        if stop_signal:
                            break
                        else:
                            continue
                if raw:
                    img.metadata = {
                        "counter": count,
                        "timestamp": img.tsSec + img.tsUSec * 1e-6,
                    }
                    stop_signal = yield img
                else:
                    stop_signal = yield MetadataArray(
                        img.get_image_data_numpy(),  # no copy
                        metadata={
                            "counter": count,
                            "timestamp": img.tsSec + img.tsUSec * 1e-6,
                        },
                    )
                count += 1
                if stop_signal:
                    break
        finally:
            if wait_before_stopping is not None:
                print()
                print("Wait before releasing the camera...")
                await wait_before_stopping()
            self.cam.stop_acquisition()
        if stop_signal:
            yield True
            
    def xidngFillMetadataFromCameraParams(self):
        """Fills entire metadata structure with current camera parameter values obtained from xiGetParam calls.
        """
        f = xiapi_dng_store.xidngFillMetadataFromCameraParams
        f.argtypes = (wintypes.HANDLE, ctypes.POINTER(XI_DNG_METADATA))
        f.restype = XI_RETURN
        metadata = XI_DNG_METADATA()
        ret_code = f(self.cam.handle, ctypes.byref(metadata))
        return metadata
    
    def xidngStore(self, filename, img, camera_metadata):
        """Saves the image into the file in DNG image file format. Does not support images in planar RGB and Transport formats.
        """
        f = xiapi_dng_store.xidngStore
        f.argtypes = (ctypes.c_char_p, ctypes.POINTER(XI_IMG), ctypes.POINTER(XI_DNG_METADATA))
        f.restype = XI_RETURN
        ret_code = f(ctypes.create_string_buffer(str(filename).encode('utf-8')), ctypes.byref(img), ctypes.byref(camera_metadata))
        return ret_code
    
    async def save_dng(self, filename, img, camera_metadata=None):
        if camera_metadata is None:
            camera_metadata = self.xidngFillMetadataFromCameraParams()
        loop = asyncio.get_event_loop()
        ret_code = await loop.run_in_executor(
            None,
            self.xidngStore,
            filename,
            img,
            camera_metadata,
        )
        return ret_code
