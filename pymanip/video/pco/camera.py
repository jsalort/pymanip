"""PCO Camera module (:mod:`pymanip.video.pco.camera`)
======================================================

This module implement the :class:`pymanip.video.pco.PCO_Camera` class using
bindings to the Pixelfly library from :mod:`pymanip.video.pco.pixelfly`.

.. autoclass:: PCO_Camera
   :members:
   :private-members:

.. autofunction:: PCO_get_binary_timestamp

.. autoclass:: PCO_Buffer
   :members:
   :private-members:

"""

import sys
import itertools
import ctypes
import datetime
import win32event

import numpy as np
import asyncio

from pymanip.video import MetadataArray, Camera, CameraTimeout
import pymanip.video.pco.pixelfly as pf


def PCO_get_binary_timestamp(image):
    """This functions reads the BCD coded timestamp in the first 14 pixels of an image
    from a PCO camera.

    :param image: the PCO camera image buffer
    :type image: array
    :return: counter, timestamp
    :rtype: int, datetime

    We assume the following format (per PCO documentation):

    ========= =================== ======
    Pixel     Description         Range
    ========= =================== ======
    Pixel  1  Image counter (MSB) 00..99
    Pixel  2  Image counter       00..99
    Pixel  3  Image counter       00..99
    Pixel  4  Image counter (LSB) 00..99
    Pixel  5  Year (MSB)          20
    Pixel  6  Year (LSB)          03..99
    Pixel  7  Month               01..12
    Pixel  8  Day                 01..31
    Pixel  9  Hour                00..23
    Pixel 10  Minutes             00..59
    Pixel 11  Seconds             00..59
    Pixel 12  µs * 10000          00..99
    Pixel 13  µs * 100            00..99
    Pixel 14  µs                  00..90
    ========= =================== ======

    """
    counter = pf.bcd_to_int(image[:4], endianess="big")
    year = pf.bcd_to_int(image[4:6], endianess="big")
    month = pf.bcd_to_int(image[6])
    day = pf.bcd_to_int(image[7])
    hour = pf.bcd_to_int(image[8])
    minutes = pf.bcd_to_int(image[9])
    seconds = pf.bcd_to_int(image[10])
    microseconds = pf.bcd_to_int(image[11:], endianess="big")
    return (
        counter,
        datetime.datetime(year, month, day, hour, minutes, seconds, microseconds),
    )


class PCO_Buffer:
    """This class represents an allocated buffer for the PCO camera.
    It implements context manager, as well as utility function to convert to bytes
    and numpy array. The buffer is allocated in the constructor method, and freed
    either by the context manager exit method, or manually calling the :meth:`free`
    method.

    :param cam_handle: camera handle
    :type cam_handle: HANDLE
    :param XResAct: resolution in x direction
    :type XResAct: int
    :param YResAct: resolution in y direction
    :type YResAct: int
    """

    def __init__(self, cam_handle, XResAct, YResAct):
        """Constructor method
        """
        self.cam_handle = cam_handle
        self.XResAct = XResAct
        self.YResAct = YResAct
        bufSizeInBytes = XResAct * YResAct * ctypes.sizeof(ctypes.wintypes.WORD)

        self.bufPtr = ctypes.POINTER(ctypes.wintypes.WORD)()
        num, event = pf.PCO_AllocateBuffer(cam_handle, -1, bufSizeInBytes, self.bufPtr)
        self.bufNr = num
        self.event_handle = event

    def free(self):
        """This methods frees the buffer.
        """
        pf.PCO_FreeBuffer(self.cam_handle, self.bufNr)
        self.bufPtr = None

    def __enter__(self):
        """Context manager enter method
        """
        return self

    def __exit__(self, type_, value, cb):
        """Context manager exit method
        """
        self.free()

    def as_array(self):
        """This methods returns the buffer as a numpy array. No data is copied,
        the memory is still bound to this buffer. The user must copy the data if
        necessary.

        :return: image array
        :rtype: numpy.ndarray

        """
        return np.ctypeslib.as_array(self.bufPtr, shape=(self.YResAct, self.XResAct))

    def bytes(self):
        """This methods returns the data as a bytearray.

        :return: image data
        :rtype: bytearray

        """
        nval = self.XResAct * self.YResAct
        bufType = ctypes.wintypes.WORD * nval
        return bytearray(bufType.from_address(ctypes.addressof(self.bufPtr.contents)))


class PCO_Camera(Camera):
    """Concrete :class:`pymanip.video.Camera` class for PCO camera.

    :param interface: interface where to look for the camera, defaults to "all"
    :type interface: str, optional
    :param camera_num: camera number to look for, defaults to 0.
    :type camera_num: int, optional
    :param metadata_mode: enable PCO Metadata mode, defaults to False.
    :type metadata_mode: bool, optional
    :param timestamp_mode: enable Timestamp mode (supported by all cameras), defaults to True.
    :type timestamp_mode: bool, optional

    """

    def __init__(
        self, interface="all", camera_num=0, *, metadata_mode=False, timestamp_mode=True
    ):
        """Constructor method

        .. note::
            pco.sdk_manual page 10:
            First step is to PCO_OpenCamera
            As next step camera description and status should be queried
            by calling PCO_GetCameraDescription and PCO_GetCameraHealthStatus
        """

        print("interface =", interface)
        print("camera_num =", camera_num)

        self.handle = pf.PCO_OpenCameraEx(interface, camera_num)
        self.camera_description = pf.PCO_GetCameraDescription(self.handle)
        warn, err, status = self.health_status()
        if warn or err:
            print("Warning bits :", warn)
            print("Error bits :", err)
        else:
            print("Connected to", pf.PCO_GetInfoString(self.handle))
            print("Status bits :", status)
        pf.PCO_SetBitAlignment(self.handle, sys.byteorder == "little")
        self.metadata_mode = metadata_mode
        self.timestamp_mode = timestamp_mode
        if timestamp_mode:
            # Timestamp is supported by all cameras but the information
            # is written on the first 14 pixels of the transfered image
            pf.PCO_SetTimestampMode(
                self.handle, 0x0001
            )  # binary mode (BCD coded in the first 14 px)
        else:
            pf.PCO_SetTimestampMode(self.handle, 0x0000)
        if metadata_mode:
            # MetaData is supported on pco.dimax and pco.edge only
            MetaDataSize, MetaDataVersion = pf.PCO_SetMetaDataMode(self.handle, True)
            self.MetaDataSize = MetaDataSize
            self.MetaDataVersion = MetaDataVersion

    def close(self):
        """This method closes the connection to the camera.
        """
        pf.PCO_CloseCamera(self.handle)
        self.handle = None
        print("Connection to camera closed.")

    def __exit__(self, type_, value, cb):
        """Context manager exit method
        """
        super(PCO_Camera, self).__exit__(type_, value, cb)
        self.close()

    # Query states
    def health_status(self):
        """This method queries the camera for its health status.

        :return: warn, err, status
        """
        warn, err, status = pf.PCO_GetCameraHealthStatus(self.handle)
        return warn, err, status

    # Set camera settings
    def set_adc_operating_mode(self, mode):
        """This function selects single or dual ADC operating mode:

           :param mode: "single" (or 0x0001) or "dual" (or 0x0002)
           :type mode: int or str

           - Single mode increases linearity;

           - Dual mode allows higher frame rates.

        """
        if mode not in (0x0001, 0x0002):
            shortcut = {"single": 0x0001, "dual": 0x0002}
            mode = shortcut[mode]
        pf.PCO_SetADCOperation(self.handle, mode)

    def set_pixel_rate(self, rate):
        """This function selects the pixel rate for sensor readout.

        :param rate: readout rate (in Hz)
        :type rate: float

        For PCO.1600: 10 Mhz or 40 MHz
        """
        pf.PCO_SetPixelRate(self.handle, int(rate))

    def set_trigger_mode(self, mode):
        """This method sets the trigger mode for the camera.

        :param mode: one of PCO_TriggerModeDescription
        :type mode: str

        Possible values are:

        ======= ==============================================
        mode    description
        ======= ==============================================
        0x0000  auto sequence
        0x0001  software trigger
        0x0002  external exposure start & software trigger
        0x0003  external exposure control
        0x0004  external synchronized
        0x0005  fast external exposure control
        0x0006  external CDS control
        0x0007  slow external exposure control
        0x0102  external synchronized HDSDI
        ======= ==============================================

        """

        if isinstance(mode, bool):
            if mode:
                self.set_trigger_mode(0x0002)
            else:
                self.set_trigger_mode(0x0000)
        elif mode in pf.PCO_TriggerModeDescription:
            pf.PCO_SetTriggerMode(self.handle, mode)
        else:
            for key, val in pf.PCO_TriggerModeDescription.items():
                if val == mode:
                    break
            else:
                raise ValueError("Unknown trigger mode : " + str(mode))
            pf.PCO_SetTriggerMode(self.handle, key)

    def set_delay_exposuretime(self, delay=None, exposuretime=None):
        """This method sets both the delay and the exposure time.

        :param delay: delay in seconds
        :type delay: float
        :param exposuretime: exposure time in seconds
        :type exposuretime: float
        """
        if delay is None or exposuretime is None:
            (
                delay_current,
                exposure_current,
                tb_delay,
                tb_exposure,
            ) = pf.PCO_GetDelayExposureTime(self.handle)
        if delay is None:
            delay = delay_current
        else:
            delay = delay * 1000
            tb_delay = 0x0002
            if delay < 1.0:
                delay = delay * 1000
                tb_delay = 0x0001
                if delay < 1.0:
                    delay = delay * 1000
                    tb_delay = 0x0000
        if exposuretime is None:
            exposuretime = exposure_current
        else:
            exposuretime = exposuretime * 1000
            tb_exposure = 0x0002
            if exposuretime < 1.0:
                exposuretime = exposuretime * 1000
                tb_exposure = 0x0001
                if exposuretime < 1.0:
                    exposuretime = exposuretime * 1000
                    tb_exposure = 0x0000
        units = {0x0000: "ns", 0x0001: "µs", 0x0002: "ms"}
        print("Setting delay to", int(delay), units[tb_delay])
        print("Setting exposure time to", int(exposuretime), units[tb_exposure])
        pf.PCO_SetDelayExposureTime(
            self.handle, int(delay), int(exposuretime), tb_delay, tb_exposure
        )

    def set_roi(self, roiX0=0, roiY0=0, roiX1=0, roiY1=0):
        r"""This method sets the positions of the upper left corner (X0,Y0) and lower right
        (X1,Y1) corner of the ROI (region of interest) in pixels.

        :param roiX0: left border in pixels, must be :math:`1 + 32n, n \in \mathbb{N}`
        :type roiX0: int
        :param roiY0: top border in pixels, must be :math:`1 + 8n, n \in \mathbb{N}`
        :type roiY0`: int
        :param roiX1: right border in pixels, must be :math:`32m, m \in \mathbb{N}`
        :type roiX1: int
        :param roiY1: bottom border in pixels, must be :math:`8m, m \in \mathbb{N}`

        The minimum ROI is :math:`64\times 16` pixels, and it is required that :math:`roiX1 \geq roix0` and :math:`roiY1 \geq roiY0`.
        """
        if (roiX0 - 1) % 32 != 0 or roiX1 % 32 != 0:
            raise ValueError("X0 must be 1+32n, X1 must be 32m, n, m integers")
        if (roiY0 - 1) % 8 != 0 or roiY1 % 8 != 0:
            raise ValueError("Y0 must be 1+8n, Y1 must be 8m, n, m integers")
        if roiX1 - roiX0 + 1 < 64 or roiY1 - roiY0 + 1 < 16:
            raise ValueError("Minimum ROI is 64 x 16 pixels")
        if roiX0 >= roiX1 or roiY0 >= roiY1:
            raise ValueError(
                "ROI expected xmin, ymin, xmax, ymax with xmax > xmin and ymax > ymin"
            )
        print(
            "Setting the ROI to (X0,Y0,X1,Y1)",
            int(roiX0),
            int(roiY0),
            int(roiX1),
            int(roiY1),
        )
        pf.PCO_SetROI(self.handle, int(roiX0), int(roiY0), int(roiX1), int(roiY1))

    def set_frame_rate(self, Frameratemode, Framerate, Framerateexposure):
        """This method sets Frame rate (mHz) and exposure time (ns).

        :param Frameratemode: one of the possible framerate modes (0x0000, 0x0001, 0x0002, 0x0003)
        :type Frameratemode: int
        :param Framerate: framerate in mHz
        :type Framerate: int
        :param Framerateexposure: Exposure time in ns
        :type Framerateexposure: int

        :return: message, framerate, exposure time
        :rtype: int, int, int

        The meaning of the framerate mode is given in this table

        ==============  =====================================================================
        Framerate mode  Meaning
        ==============  =====================================================================
        0x0000          Auto mode (camera decides which parameter will be trimmed)
        0x0001          Frame rate has priority, (exposure time will be trimmed)
        0x0002          Exposure time has priority, (frame rate will be trimmed)
        0x0003          Strict, function shall return with error if values are not possible.
        ==============  =====================================================================

        The message value in return gives the limiting factors when the condition are not fulfilled.
        The meaning is given in this table

        ==============  =========================================================================
        Message         Meaning
        ==============  =========================================================================
        0x0000          Settings consistent, all conditions met
        0x0001          Frame rate trimmed, frame rate was limited by readout time
        0x0002          Frame rate trimmed, frame rate was limited by exposure time
        0x0004          Exposure time trimmed, exposure time cut to frame time
        0x8000          Return values dwFrameRate and dwFrameRateExposure are not yet validated.
        ==============  =========================================================================

        In the case where message 0x8000 is returned, the other values returned are simply
        the parameter values passed to the function.
        """
        print(
            "Setting the frame rate and the exposure time to",
            Framerate,
            Framerateexposure,
        )
        message, f, te = pf.PCO_SetFrameRate(
            self.handle, Frameratemode, Framerate, Framerateexposure
        )
        return message, f, te

    def set_noise_filter_mode(self, mode):
        """This method does set the image correction operating mode of the camera. Image correction can either be switched
        totally off, noise filter only mode or noise filter plus hot pixel correction mode.
        The command will be rejected, if Recording State is [run], see PCO_GetRecordingState.

        :param mode: the noise filter mode
        :type mode: int

        The noise filter mode:

        ======= =============================
        Value   Mode
        ======= =============================
        0x0000  [off]
        0x0001  [on]
        0x0101  [on + hot pixel correction]
        ======= =============================

        """
        pf.PCO_SetNoiseFilterMode(self.handle, mode)

    def current_noise_filter_mode(self):
        """This methods queries the current noise filter mode.

        :return: the noise filter mode
        :rtype: int

        The noise filter mode:

        ======= =============================
        Value   Mode
        ======= =============================
        0x0000  [off]
        0x0001  [on]
        0x0101  [on + hot pixel correction]
        ======= =============================

        """
        return pf.PCO_GetNoiseFilterMode(self.handle)

    # Properties
    @property
    def resolution(self):
        """Camera maximum resolution
        """
        return self.camera_description.maximum_resolution_std

    @property
    def name(self):
        """Camera name
        """
        # if hasattr(self, '_name'):
        #    return self._name
        # PCO_GetCameraName is not supported by pco.1600
        # self._name = pf.PCO_GetCameraName(self.handle)
        # return self._name
        return "PCO Camera"

    @property
    def bitdepth(self):
        """Camera sensor bit depth
        """
        return 16

    def current_delay_exposure_time(self):
        """This method returns current delay and exposure time in seconds.

        :return: delay, exposure
        :rtype: float, float
        """

        delay, exposure, tb_delay, tb_exposure = pf.PCO_GetDelayExposureTime(
            self.handle
        )
        return (
            delay * pf.PCO_Timebases[tb_delay],
            exposure * pf.PCO_Timebases[tb_exposure],
        )

    def current_trigger_mode_description(self):
        """This method returns the current trigger mode description.

        :return: description of current trigger mode
        :rtype: str
        """
        return pf.PCO_TriggerModeDescription[pf.PCO_GetTriggerMode(self.handle)]

    def current_adc_operation(self):
        """This method returns the current ADC operation mode.

        :return: Current ADC operation mode (0x0001 for "single", 0x0002 for "dual")
        :rtype: int
        """
        return pf.PCO_GetADCOperation(self.handle)

    def current_pixel_rate(self):
        """This method returns the current pixel rate.

        :return: Current pixel rate (e.g. 10 MHz or 40 MHz for the PCO.1600
        :rtype: int
        """
        return pf.PCO_GetPixelRate(self.handle)

    @property
    def possible_pixel_rate(self):
        return [r for r in self.camera_description.dwPixelRateDESC]

    def current_frame_rate(self):
        """This method returns the current frame rate.

        :return: Current frame rate
        :rtype: int
        """
        return pf.PCO_GetFrameRate(self.handle)

    def acquisition_oneshot(self):
        """Concrete implementation of :meth:`pymanip.video.Camera.acquisition_oneshot` for the PCO camera.
        """
        # Arm camera
        pf.PCO_ArmCamera(self.handle)
        XResAct, YResAct, XResMax, YResMax = pf.PCO_GetSizes(self.handle)

        with PCO_Buffer(self.handle, XResAct, YResAct) as buffer:
            try:
                pf.PCO_SetImageParameters(
                    self.handle,
                    XResAct,
                    YResAct,
                    pf.IMAGEPARAMETERS_READ_WHILE_RECORDING,
                )
                pf.PCO_SetRecordingState(self.handle, True)
                pf.PCO_GetImageEx(
                    self.handle, 1, 0, 0, buffer.bufNr, XResAct, YResAct, 16
                )
                array = buffer.as_array().copy()
            finally:
                pf.PCO_SetRecordingState(self.handle, False)
                pf.PCO_CancelImages(self.handle)
        return array

    async def acquisition_async(
        self,
        num=np.inf,
        timeout=None,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
    ):
        """Concrete implementation of :meth:`pymanip.video.Camera.acquisition_async` for the PCO camera.
        """

        loop = asyncio.get_event_loop()

        if timeout is None:
            delay, exposure = self.current_delay_exposure_time()
            timeout = int(max((2000 * exposure, 1000)))

        # Arm camera
        if pf.PCO_GetRecordingState(self.handle):
            pf.PCO_SetRecordingState(self.handle, False)
        pf.PCO_ArmCamera(self.handle)
        warn, err, status = self.health_status()
        if err != 0:
            raise RuntimeError("Camera has error status!")
        XResAct, YResAct, XResMax, YResMax = pf.PCO_GetSizes(self.handle)

        with PCO_Buffer(self.handle, XResAct, YResAct) as buf1, PCO_Buffer(
            self.handle, XResAct, YResAct
        ) as buf2, PCO_Buffer(self.handle, XResAct, YResAct) as buf3, PCO_Buffer(
            self.handle, XResAct, YResAct
        ) as buf4:

            buffers = (buf1, buf2, buf3, buf4)
            try:
                pf.PCO_SetImageParameters(
                    self.handle,
                    XResAct,
                    YResAct,
                    pf.IMAGEPARAMETERS_READ_WHILE_RECORDING,
                )
                pf.PCO_SetRecordingState(self.handle, True)
                for buffer in buffers:
                    pf.PCO_AddBufferEx(
                        self.handle, 0, 0, buffer.bufNr, XResAct, YResAct, 16
                    )
                count = 0
                buffer_ring = itertools.cycle(buffers)
                while count < num:
                    if (
                        count == 0
                        and initialising_cams is not None
                        and self in initialising_cams
                    ):
                        initialising_cams.remove(self)

                    waitstat = await loop.run_in_executor(
                        None,
                        win32event.WaitForMultipleObjects,
                        [buffer.event_handle for buffer in buffers],
                        0,
                        timeout,
                    )
                    if waitstat == win32event.WAIT_TIMEOUT:
                        if raise_on_timeout:
                            raise CameraTimeout(f"Timeout ({timeout:})")
                        else:
                            stop_signal = yield None
                            if not stop_signal:
                                continue
                            else:
                                break
                    for ii, buffer in zip(range(4), buffer_ring):
                        waitstat = await loop.run_in_executor(
                            None, win32event.WaitForSingleObject, buffer.event_handle, 0
                        )
                        if waitstat == win32event.WAIT_OBJECT_0:
                            win32event.ResetEvent(buffer.event_handle)
                            statusDLL, statusDrv = pf.PCO_GetBufferStatus(
                                self.handle, buffer.bufNr
                            )
                            if statusDrv != 0:
                                raise RuntimeError(
                                    "buffer {:} error status {:}".format(
                                        buffer.bufNr, statusDrv
                                    )
                                )
                            if raw:
                                data = {"buffer": buffer.bytes()}
                                if self.timestamp_mode:
                                    counter, dt = PCO_get_binary_timestamp(
                                        buffer.bufPtr[:14]
                                    )
                                    data["counter"] = counter
                                    data["timestamp"] = dt
                                stop_signal = yield data
                            else:
                                if self.metadata_mode:
                                    metadata = pf.PCO_GetMetaData(
                                        self.handle, buffer.bufNr
                                    )
                                    stop_signal = yield MetadataArray(
                                        buffer.as_array(), metadata=metadata
                                    )
                                elif self.timestamp_mode:
                                    counter, dt = PCO_get_binary_timestamp(
                                        buffer.bufPtr[:14]
                                    )
                                    stop_signal = yield MetadataArray(
                                        buffer.as_array(),
                                        metadata={"counter": counter, "timestamp": dt},
                                    )
                                else:
                                    stop_signal = yield buffer.as_array()
                            count += 1
                            pf.PCO_AddBufferEx(
                                self.handle, 0, 0, buffer.bufNr, XResAct, YResAct, 16
                            )
                        else:
                            break
                        if stop_signal:
                            break
                    if stop_signal:
                        break
            finally:
                pf.PCO_SetRecordingState(self.handle, False)
                pf.PCO_CancelImages(self.handle)
        if stop_signal:
            yield True


if __name__ == "__main__":
    h = pf.PCO_OpenCameraEx("USB 3.0", 0)
    pf.PCO_GetInfoString(h)
    pf.PCO_CloseCamera(h)
