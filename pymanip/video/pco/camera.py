"""

This is the definition of a higher level PCO_Camera object
based on the low-level pco.pixelfly module.

"""

import sys
import itertools
import ctypes
import datetime
import win32event

import numpy as np
import asyncio
from pymanip.asynctools import synchronize_generator

from pymanip.video import MetadataArray, Camera, CameraTimeout
import pymanip.video.pco.pixelfly as pf


def PCO_get_binary_timestamp(image):
    """
    Reads the BCD coded timestamp in the first 14 pixels of an image

    Format:
    Pixel  1: Image counter (MSB) 00..99
    Pixel  2: Image counter       00..99
    Pixel  3: Image counter       00..99
    Pixel  4: Image counter (LSB) 00..99
    Pixel  5: Year (MSB)          20
    Pixel  6: Year (LSB)          03..99
    Pixel  7: Month               01..12
    Pixel  8: Day                 01..31
    Pixel  9: Hour                00..23
    Pixel 10: Minutes             00..59
    Pixel 11: Seconds             00..59
    Pixel 12: µs * 10000          00..99
    Pixel 13: µs * 100            00..99
    Pixel 14: µs                  00..90
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
    def __init__(self, cam_handle, XResAct, YResAct):
        self.cam_handle = cam_handle
        self.XResAct = XResAct
        self.YResAct = YResAct
        bufSizeInBytes = XResAct * YResAct * ctypes.sizeof(ctypes.wintypes.WORD)

        self.bufPtr = ctypes.POINTER(ctypes.wintypes.WORD)()
        num, event = pf.PCO_AllocateBuffer(cam_handle, -1, bufSizeInBytes, self.bufPtr)
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

    def bytes(self):
        nval = self.XResAct * self.YResAct
        bufType = ctypes.wintypes.WORD * nval
        return bytearray(bufType.from_address(ctypes.addressof(self.bufPtr.contents)))


class PCO_Camera(Camera):

    # Open/Close camera
    def __init__(
        self, interface="all", camera_num=0, *, metadata_mode=False, timestamp_mode=True
    ):
        """
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
        pf.PCO_CloseCamera(self.handle)
        self.handle = None
        print("Connection to camera closed.")

    def __exit__(self, type_, value, cb):
        super(PCO_Camera, self).__exit__(type_, value, cb)
        self.close()

    # Query states
    def health_status(self):
        warn, err, status = pf.PCO_GetCameraHealthStatus(self.handle)
        return warn, err, status

    # Set camera settings
    def set_adc_operating_mode(self, mode):
        """
        Select single or dual ADC operating mode.
        Single mode increases linearity;
        Dual mode allows higher frame rates.
        """
        if mode not in (0x0001, 0x0002):
            shortcut = {"single": 0x0001, "dual": 0x0002}
            mode = shortcut[mode]
        pf.PCO_SetADCOperation(self.handle, mode)

    def set_pixel_rate(self, rate):
        """
        Select pixel rate for sensor readout (in Hz)
        For PCO.1600: 10 Mhz or 40 MHz
        """
        pf.PCO_SetPixelRate(self.handle, int(rate))

    def set_trigger_mode(self, mode):
        if mode in pf.PCO_TriggerModeDescription:
            pf.PCO_SetTriggerMode(self.handle, mode)
        else:
            for key, val in pf.PCO_TriggerModeDescription.items():
                if val == mode:
                    break
            else:
                raise ValueError("Unknown trigger mode : " + str(mode))
            pf.PCO_SetTriggerMode(self.handle, key)

    def set_delay_exposuretime(self, delay=None, exposuretime=None):
        """
        delay and exposuretime in seconds
        """
        if delay is None or exposuretime is None:
            delay_current, exposure_current, tb_delay, tb_exposure = pf.PCO_GetDelayExposureTime(
                self.handle
            )
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
        """
        Positions of the upper left corner (X0,Y0) and lower right
        (X1,Y1) corner of the ROI (region of interest) in pixels.
        """
        if (roiX0 - 1) % 32 != 0 or roiX1 % 32 != 0:
            raise ValueError("X0 must be 1+32n, X1 must be 32m, n, m entiers")
        if (roiY0 - 1) % 8 != 0 or roiY1 % 8 != 0:
            raise ValueError("Y0 must be 1+8n, Y1 must be 8m, n, m entiers")
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
        """
        Sets Frame rate (mHz) and exposure time (ns)
        Frame rate status gives the limiting factors
        if the condition are not met.
        Frame rate mode variable to set the frame rate mode:
        • 0x0000= Auto mode (camera decides which parameter will be trimmed)
        • 0x0001= Frame rate has priority, (exposure time will be trimmed)
        • 0x0002= Exposure time has priority, (frame rate will be trimmed)
        • 0x0003= Strict, function shall return with error if values are not possible.
        Message returns:
          0x0000= Settings consistent, all conditions met
        • 0x0001= Frame rate trimmed, frame rate was limited by readout time
        • 0x0002= Frame rate trimmed, frame rate was limited by exposure time
        • 0x0004= Exposure time trimmed, exposure time cut to frame time
        • 0x8000= Return values dwFrameRate and dwFrameRateExposure are not
        yet validated. In that case, the values returned are the values passed
        to the function
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

    # Properties
    @property
    def resolution(self):
        return self.camera_description.maximum_resolution_std

    @property
    def name(self):
        # if hasattr(self, '_name'):
        #    return self._name
        # PCO_GetCameraName is not supported by pco.1600
        # self._name = pf.PCO_GetCameraName(self.handle)
        # return self._name
        return "PCO Camera"

    @property
    def bitdepth(self):
        return 16

    def current_delay_exposure_time(self):
        """
        returns current delay and exposure time in seconds
        """

        delay, exposure, tb_delay, tb_exposure = pf.PCO_GetDelayExposureTime(
            self.handle
        )
        return (
            delay * pf.PCO_Timebases[tb_delay],
            exposure * pf.PCO_Timebases[tb_exposure],
        )

    def current_trigger_mode_description(self):
        return pf.PCO_TriggerModeDescription[pf.PCO_GetTriggerMode(self.handle)]

    def current_adc_operation(self):
        return pf.PCO_ADCOperation(self.handle)

    def current_pixel_rate(self):
        return pf.PCO_GetPixelRate(self.handle)

    def current_frame_rate(self):
        return pf.PCO_GetFrameRate(self.handle)

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

    def acquisition(self, num=np.inf, timeout=None, raw=False, raise_on_timeout=True):
        yield from synchronize_generator(
            self.acquisition_async, num, timeout, raw, None, raise_on_timeout
        )

    async def acquisition_async(
        self,
        num=np.inf,
        timeout=None,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
    ):
        """
        Multiple image acquisition
        yields a shared memory numpy array valid only
        before generator object cleanup.

        timeout in milliseconds
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
