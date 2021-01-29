"""Ximea Camera module (:mod:`pymanip.video.ximea.camera`)
==========================================================

This module implements the :class:`pymanip.video.ximea.Ximea_Camera` using the
`Python module provided by Ximea <https://www.ximea.com/support/wiki/apis/Python_inst_win>`_.

.. autoclass:: Ximea_Camera
   :members:
   :private-members:
   :show-inheritance:

"""

import asyncio
import ctypes

import numpy as np
from pymanip.video import MetadataArray, Camera, CameraTimeout

from ximea import xiapi
from ximea.xidefs import XI_IMG_FORMAT, XI_TRG_SOURCE, XI_TRG_SELECTOR


class Ximea_Camera(Camera):
    """Concrete :class:`pymanip.video.Camera` class for AVT camera.
    """

    color_order = "BGR"  # Ximea RGB mode is [blue][green][red] per the doc.

    def __init__(self, serial_number=None, pixelFormat=None):
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
        print(f"Camera {self.name:} opened ({pixelFormat:})")

    def close(self):
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
        """Set external trigger
        """
        if external:
            self.cam.set_gpi_mode("XI_GPI_TRIGGER")
            self.cam.set_trigger_source("XI_TRG_LEVEL_HIGH")
            self.cam.set_trigger_selector("XI_TRG_SEL_EXPOSURE_START")
        else:
            self.cam.set_trigger_source("XI_TRG_OFF")

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
    ):
        """Concrete implementation of :meth:`pymanip.video.Camera.acquisition_async` for the Ximea camera.

        timeout in milliseconds.
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
            self.cam.stop_acquisition()
        if stop_signal:
            yield True
