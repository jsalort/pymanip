"""IDS Camera module (:mod:`pymanip.video.ids`)
===============================================

This module implements the :class:`pymanip.video.ids.IDS_Camera` class
using the third-party :mod:`pyueye` module.

.. autoclass:: IDS_Camera
   :members:
   :private-members:
   :show-inheritance:

"""

from datetime import datetime
import asyncio
import ctypes

import numpy as np
from pyueye import ueye
from pymanip.video import MetadataArray, Camera, CameraTimeout


class IDS_Camera(Camera):
    """Concrete implementation for IDS Camera.
    """

    def __init__(self, cam_num=0):
        self.name = f"IDS Camera {cam_num:}"
        self.hCam = ueye.HIDS(cam_num)

        self.sInfo = ueye.SENSORINFO()
        self.cInfo = ueye.CAMINFO()
        self.pcImageMemory = ueye.c_mem_p()
        self.MemID = ueye.int()
        self.rectAOI = ueye.IS_RECT()
        self.pitch = ueye.INT()
        self.nBitsPerPixel = ueye.INT(
            24
        )  # 24: bits per pixel for color mode; take 8 bits per pixel for monochrome
        self.channels = (
            3  # 3: channels for color mode(RGB); take 1 channel for monochrome
        )
        self.m_nColorMode = ueye.INT()  # Y8/RGB16/RGB24/REG32
        self.bytes_per_pixel = int(self.nBitsPerPixel / 8)

        # Starts the driver and establishes the connection to the camera
        nRet = ueye.is_InitCamera(self.hCam, None)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError(f"is_InitCamera ERROR {nRet:}")

        # Reads out the data hard-coded in the non-volatile camera memory and writes it to the data structure that cInfo points to
        nRet = ueye.is_GetCameraInfo(self.hCam, self.cInfo)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_GetCameraInfo ERROR")

        # You can query additional information about the sensor type used in the camera
        nRet = ueye.is_GetSensorInfo(self.hCam, self.sInfo)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_GetSensorInfo ERROR")

        nRet = ueye.is_ResetToDefault(self.hCam)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_ResetToDefault ERROR")

        # Set display mode to DIB
        nRet = ueye.is_SetDisplayMode(self.hCam, ueye.IS_SET_DM_DIB)

        # Set the right color mode
        if (
            int.from_bytes(self.sInfo.nColorMode.value, byteorder="big")
            == ueye.IS_COLORMODE_BAYER
        ):
            # setup the color depth to the current windows setting
            ueye.is_GetColorDepth(self.hCam, self.nBitsPerPixel, self.m_nColorMode)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            print("IS_COLORMODE_BAYER: ")
            print("\tm_nColorMode: \t\t", self.m_nColorMode)
            print("\tnBitsPerPixel: \t\t", self.nBitsPerPixel)
            print("\tbytes_per_pixel: \t\t", self.bytes_per_pixel)
            print()

        elif (
            int.from_bytes(self.sInfo.nColorMode.value, byteorder="big")
            == ueye.IS_COLORMODE_CBYCRY
        ):
            # for color camera models use RGB32 mode
            self.m_nColorMode = ueye.IS_CM_BGRA8_PACKED
            self.nBitsPerPixel = ueye.INT(32)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            print("IS_COLORMODE_CBYCRY: ")
            print("\tm_nColorMode: \t\t", self.m_nColorMode)
            print("\tnBitsPerPixel: \t\t", self.nBitsPerPixel)
            print("\tbytes_per_pixel: \t\t", self.bytes_per_pixel)
            print()

        elif (
            int.from_bytes(self.sInfo.nColorMode.value, byteorder="big")
            == ueye.IS_COLORMODE_MONOCHROME
        ):
            # for color camera models use RGB32 mode
            self.m_nColorMode = ueye.IS_CM_MONO8
            self.nBitsPerPixel = ueye.INT(8)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            print("IS_COLORMODE_MONOCHROME: ")
            print("\tm_nColorMode: \t\t", self.m_nColorMode)
            print("\tnBitsPerPixel: \t\t", self.nBitsPerPixel)
            print("\tbytes_per_pixel: \t\t", self.bytes_per_pixel)
            print()

        else:
            # for monochrome camera models use Y8 mode
            self.m_nColorMode = ueye.IS_CM_MONO8
            self.nBitsPerPixel = ueye.INT(8)
            self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
            # print("else")

        # Can be used to set the size and position of an "area of interest"(AOI) within an image
        nRet = ueye.is_AOI(
            self.hCam,
            ueye.IS_AOI_IMAGE_GET_AOI,
            self.rectAOI,
            ueye.sizeof(self.rectAOI),
        )
        if nRet != ueye.IS_SUCCESS:
            print("is_AOI ERROR")

        self.width = self.rectAOI.s32Width
        self.height = self.rectAOI.s32Height

        # Prints out some information about the camera and the sensor
        print("Camera model:\t\t", self.sInfo.strSensorName.decode("utf-8"))
        print("Camera serial no.:\t", self.cInfo.SerNo.decode("utf-8"))
        print("Maximum image width:\t", self.width)
        print("Maximum image height:\t", self.height)
        print()

        nRet = ueye.is_AllocImageMem(
            self.hCam,
            self.width,
            self.height,
            self.nBitsPerPixel,
            self.pcImageMemory,
            self.MemID,
        )
        if nRet != ueye.IS_SUCCESS:
            print("is_AllocImageMem ERROR")
        else:
            # Makes the specified image memory the active memory
            nRet = ueye.is_SetImageMem(self.hCam, self.pcImageMemory, self.MemID)
            if nRet != ueye.IS_SUCCESS:
                print("is_SetImageMem ERROR")
            else:
                # Set the desired color mode
                nRet = ueye.is_SetColorMode(self.hCam, self.m_nColorMode)

    def close(self):
        ueye.is_ExitCamera(self.hCam)

    def __exit__(self, type_, value, cb):
        """Context manager exit method
        """
        super(IDS_Camera, self).__exit__(type_, value, cb)
        self.close()

    def acquisition_oneshot(self, timeout_ms=1000):
        nRet = ueye.is_EnableEvent(self.hCam, ueye.IS_SET_EVENT_FRAME)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_EnableEvent ERROR")

        nRet = ueye.is_FreezeVideo(self.hCam, ueye.IS_DONT_WAIT)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_CaptureVideo ERROR")
        nRet = ueye.is_WaitEvent(self.hCam, ueye.IS_SET_EVENT_FRAME, timeout_ms)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_WaitEvent ERROR")

        nRet = ueye.is_InquireImageMem(
            self.hCam,
            self.pcImageMemory,
            self.MemID,
            self.width,
            self.height,
            self.nBitsPerPixel,
            self.pitch,
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_InquireImageMem ERROR")
        array = ueye.get_data(
            self.pcImageMemory,
            self.width,
            self.height,
            self.nBitsPerPixel,
            self.pitch,
            copy=True,
        )

        nRet = ueye.is_DisableEvent(self.hCam, ueye.IS_SET_EVENT_FRAME)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_DisableEvent ERROR")

        return array.reshape((self.height.value, self.width.value))

    async def acquisition_async(
        self,
        num=np.inf,
        timeout=1000,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
    ):
        """Concrete implementation
        """
        loop = asyncio.get_event_loop()

        nRet = ueye.is_CaptureVideo(self.hCam, ueye.IS_DONT_WAIT)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("is_CaptureVideo ERROR")

        try:
            nRet = ueye.is_InquireImageMem(
                self.hCam,
                self.pcImageMemory,
                self.MemID,
                self.width,
                self.height,
                self.nBitsPerPixel,
                self.pitch,
            )
            image_info = ueye.UEYEIMAGEINFO()
            if nRet != ueye.IS_SUCCESS:
                raise RuntimeError("is_InquireImageMem ERROR")

            count = 0
            while count < num:
                nRet = ueye.is_EnableEvent(self.hCam, ueye.IS_SET_EVENT_FRAME)
                if nRet != ueye.IS_SUCCESS:
                    raise RuntimeError("is_EnableEvent ERROR")
                nRet = await loop.run_in_executor(
                    None, ueye.is_WaitEvent, self.hCam, ueye.IS_SET_EVENT_FRAME, timeout
                )
                if nRet == ueye.IS_TIMED_OUT:
                    if raise_on_timeout:
                        raise RuntimeError("Timeout")
                    else:
                        stop_signal = yield None
                        if stop_signal:
                            break
                        else:
                            continue
                elif nRet != ueye.IS_SUCCESS:
                    raise RuntimeError("is_WaitEvent ERROR")
                array = ueye.get_data(
                    self.pcImageMemory,
                    self.width,
                    self.height,
                    self.nBitsPerPixel,
                    self.pitch,
                    copy=False,
                )

                nRet = ueye.is_GetImageInfo(
                    self.hCam, self.MemID, image_info, ctypes.sizeof(image_info)
                )
                if nRet != ueye.IS_SUCCESS:
                    raise RuntimeError("is_GetImageInfo ERROR")

                count = count + 1
                ts = datetime(
                    image_info.TimestampSystem.wYear.value,
                    image_info.TimestampSystem.wMonth.value,
                    image_info.TimestampSystem.wDay.value,
                    image_info.TimestampSystem.wHour.value,
                    image_info.TimestampSystem.wMinute.value,
                    image_info.TimestampSystem.wSecond.value,
                    image_info.TimestampSystem.wMilliseconds * 1000,
                )
                stop_signal = yield MetadataArray(
                    array.reshape((self.height.value, self.width.value)),
                    metadata={"counter": count, "timestamp": ts.timestamp()},
                )
                if stop_signal:
                    break

        finally:
            nRet = ueye.is_StopLiveVideo(self.hCam, ueye.IS_DONT_WAIT)
            if nRet != ueye.IS_SUCCESS:
                raise RuntimeError("is_StopLiveVideo ERROR")
            nRet = ueye.is_DisableEvent(self.hCam, ueye.IS_SET_EVENT_FRAME)
            if nRet != ueye.IS_SUCCESS:
                raise RuntimeError("is_DisableEvent ERROR")
        if stop_signal:
            yield True

    def possible_pixelclock(self):
        """Query the possible values for pixelclock (in MHz)
        """

        nPixelclocks = ueye.UINT()
        nRet = ueye.is_PixelClock(
            self.hCam,
            ueye.IS_PIXELCLOCK_CMD_GET_NUMBER,
            nPixelclocks,
            ctypes.sizeof(nPixelclocks),
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_PIXELCLOCK_CMD_GET_NUMBER failed")
        if nPixelclocks.value == 0:
            return []
        pixelclock_list = (ueye.UINT * nPixelclocks.value)()
        nRet = ueye.is_PixelClock(
            self.hCam,
            ueye.IS_PIXELCLOCK_CMD_GET_LIST,
            pixelclock_list,
            ctypes.sizeof(pixelclock_list),
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_PIXELCLOCK_CMD_GET_LIST failed")
        return [pc.value for pc in pixelclock_list]

    def set_pixelclock(self, pixelclock):
        """Set the pixelclock (in MHz)
        """
        pc = ueye.UINT(int(pixelclock))
        nRet = ueye.is_PixelClock(
            self.hCam, ueye.IS_PIXELCLOCK_CMD_SET, pc, ctypes.sizeof(pc)
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_PIXELCLOCK_CMD_SET failed")
        return pc.value

    def current_pixelclock(self):
        """Queries the current pixelclock (in MHz)
        """
        pc = ueye.UINT()
        nRet = ueye.is_PixelClock(
            self.hCam, ueye.IS_PIXELCLOCK_CMD_GET, pc, ctypes.sizeof(pc)
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_PIXELCLOCK_CMD_GET failed")
        return pc.value

    def possible_exposure_time(self):
        """Query the min, max and increment in ms
        """
        min_ms = ctypes.c_double()
        max_ms = ctypes.c_double()
        inc_ms = ctypes.c_double()
        nRet = ueye.is_Exposure(
            self.hCam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN,
            min_ms,
            ctypes.sizeof(min_ms),
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MIN failed")
        nRet = ueye.is_Exposure(
            self.hCam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX,
            max_ms,
            ctypes.sizeof(max_ms),
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_MAX failed")
        nRet = ueye.is_Exposure(
            self.hCam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_INC,
            inc_ms,
            ctypes.sizeof(inc_ms),
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_EXPOSURE_CMD_GET_EXPOSURE_RANGE_INC failed")
        return min_ms.value, max_ms.value, inc_ms.value

    def current_exposure_time(self):
        """Query the current exposure time in ms
        """
        exposure_ms = ctypes.c_double()
        nRet = ueye.is_Exposure(
            self.hCam,
            ueye.IS_EXPOSURE_CMD_GET_EXPOSURE,
            exposure_ms,
            ctypes.sizeof(exposure_ms),
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_EXPOSURE_CMD_GET_EXPOSURE failed")

        return exposure_ms.value

    def set_exposure_time(self, exposure_ms):
        """Sets exposure time in ms.
        If 0 is passed, the exposure time is set to the maximum value of 1/frame rate.
        """
        exposure_ms_double = ctypes.c_double(exposure_ms)
        nRet = ueye.is_Exposure(
            self.hCam,
            ueye.IS_EXPOSURE_CMD_SET_EXPOSURE,
            exposure_ms_double,
            ctypes.sizeof(exposure_ms_double),
        )
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("IS_EXPOSURE_CMD_SET_EXPOSURE failed")
        actual = exposure_ms_double.value
        if actual != exposure_ms:
            print("Warning: actual value of exposure time is", actual, "ms")

    def set_frame_rate(self, framerate_fps):
        """Sets the framerate in frames per seconds
        """
        newFPS = ctypes.c_double()
        nRet = ueye.is_SetFrameRate(self.hCam, float(framerate_fps), newFPS)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("SetFrameRate failed")
        if newFPS.value != framerate_fps:
            print("Warning actual framerate is", newFPS.value)
        return newFPS.value

    def current_frame_rate(self):
        """Queries the current framerate
        """
        fps = ctypes.c_double()
        nRet = ueye.is_GetFrameRate(self.hCam, fps)
        if nRet != ueye.IS_SUCCESS:
            raise RuntimeError("GetFrameRate failed")
        return fps.value
