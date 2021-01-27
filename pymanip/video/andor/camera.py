"""Andor Camera module (:mod:`pymanip.video.andor.camera`)
==========================================================

This module implement the :class:`Andor_Camera` class, as a subclass
of the :class:`pymanip.video.Camera` base class. It uses the
third-party :mod:`pyAndorNeo` module.

.. autoclass:: Andor_Camera
   :members:
   :private-members:

"""

import time
import asyncio
import ctypes
import struct

import numpy as np
from pymanip.video import MetadataArray, Camera, CameraTimeout

import AndorNeo.SDK3Cam as SDK3Cam
import AndorNeo.SDK3 as SDK3

MODE_CONTINUOUS = 1
MODE_SINGLE_SHOT = 0

validROIS = [
    (2592, 2160, 1, 1),
    (2544, 2160, 1, 25),
    (2064, 2048, 57, 265),
    (1776, 1760, 201, 409),
    (1920, 1080, 537, 337),
    (1392, 1040, 561, 601),
    (528, 512, 825, 1033),
    (240, 256, 953, 1177),
    (144, 128, 1017, 1225),
]


def parse_metadata(buf, verbose=False):
    """
    Parse metadata at the end of buffer, happened when EnableMetadata boolean
    feature is true.(page 77 doc SDK3 manual)

    Metadata format: Frame data; CID; Length
    FrameData (CID=0), FPGA Ticks (CID=1), FrameInfo (CID=7)
    """
    LENGTH_FIELD_SIZE = 4
    CID_FIELD_SIZE = 4
    # TIMESTAMP_FIELD_SIZE = 8

    n = buf.size
    for ind in range(3):
        length = buf[n - LENGTH_FIELD_SIZE : n]
        cid = buf[n - (CID_FIELD_SIZE + LENGTH_FIELD_SIZE) : n - LENGTH_FIELD_SIZE]
        # if verbose:
        #    print('length =', length)
        #    print('cid =', cid)
        # length = length[0]+(2**8)*length[1]+(2**16)*length[2]+\
        # (2**32)*length[3]-CID_FIELD_SIZE
        # cid = cid[0]+(2**8)*cid[1]+(2**16)*cid[2]+(2**32)*cid[3]
        length = struct.unpack("<L", length)[0] - CID_FIELD_SIZE
        cid = struct.unpack("<L", cid)[0]
        data = buf[
            n
            - (CID_FIELD_SIZE + LENGTH_FIELD_SIZE + length) : n
            - (CID_FIELD_SIZE + LENGTH_FIELD_SIZE)
        ]
        if verbose:
            print("length =", length)
            print("cid =", cid)
            print("data =", data)
        if cid == 1:
            return struct.unpack("<Q", data)[0]
            # return sum([(256**i)*b for i, b in enumerate(data)])

        n -= CID_FIELD_SIZE + LENGTH_FIELD_SIZE + length


class Andor_Camera(Camera):
    """Concrete :class:`pymanip.video.Camera` class for Andor camera.

    :param camNum: camera number, defaults to 0.
    :type camNum: int, optional
    """

    def __init__(self, camNum=0):
        """Constructor method
        """

        self.camNum = camNum

        # Auto properties (bound in SDK3Cam __init__)
        self.CameraAcquiring = SDK3Cam.ATBool()
        self.SensorCooling = SDK3Cam.ATBool()
        self.MetadataEnable = SDK3Cam.ATBool()
        self.TimestampClock = SDK3Cam.ATInt()
        self.TimestampClockFrequency = SDK3Cam.ATInt()

        self.AcquisitionStart = SDK3Cam.ATCommand()
        self.AcquisitionStop = SDK3Cam.ATCommand()

        self.CycleMode = SDK3Cam.ATEnum()
        self.ElectronicShutteringMode = SDK3Cam.ATEnum()
        self.FanSpeed = SDK3Cam.ATEnum()
        self.PreAmpGainChannel = SDK3Cam.ATEnum()
        self.PixelEncoding = SDK3Cam.ATEnum()
        self.PixelReadoutRate = SDK3Cam.ATEnum()
        self.PreAmpGain = SDK3Cam.ATEnum()
        self.PreAmpGainSelector = SDK3Cam.ATEnum()
        self.TriggerMode = SDK3Cam.ATEnum()

        self.AOIHeight = SDK3Cam.ATInt()
        self.AOILeft = SDK3Cam.ATInt()
        self.AOITop = SDK3Cam.ATInt()
        self.AOIWidth = SDK3Cam.ATInt()
        self.AOIStride = SDK3Cam.ATInt()
        self.FrameCount = SDK3Cam.ATInt()
        self.ImageSizeBytes = SDK3Cam.ATInt()
        self.SensorHeight = SDK3Cam.ATInt()
        self.SensorWidth = SDK3Cam.ATInt()

        self.CameraModel = SDK3Cam.ATString()
        self.SerialNumber = SDK3Cam.ATString()

        self.ExposureTime = SDK3Cam.ATFloat()
        self.FrameRate = SDK3Cam.ATFloat()
        self.SensorTemperature = SDK3Cam.ATFloat()
        self.TargetSensorTemperature = SDK3Cam.ATFloat()

        self.Overlap = SDK3Cam.ATBool()
        self.SpuriousNoiseFilter = SDK3Cam.ATBool()

        self.CameraDump = SDK3Cam.ATCommand()
        self.SoftwareTrigger = SDK3Cam.ATCommand()

        self.TemperatureControl = SDK3Cam.ATEnum()
        self.TemperatureStatus = SDK3Cam.ATEnum()
        self.SimplePreAmpGainControl = SDK3Cam.ATEnum()
        self.BitDepth = SDK3Cam.ATEnum()

        self.ActualExposureTime = SDK3Cam.ATFloat()
        self.BurstRate = SDK3Cam.ATFloat()
        self.ReadoutTime = SDK3Cam.ATFloat()

        self.AccumulateCount = SDK3Cam.ATInt()
        self.BaselineLevel = SDK3Cam.ATInt()
        self.BurstCount = SDK3Cam.ATInt()
        self.LUTIndex = SDK3Cam.ATInt()
        self.LUTValue = SDK3Cam.ATInt()

        self.ControllerID = SDK3Cam.ATString()
        self.FirmwareVersion = SDK3Cam.ATString()

        # Initialisation
        self.handle = SDK3.Open(self.camNum)
        for name, var in self.__dict__.items():
            if isinstance(var, SDK3Cam.ATProperty):
                var.connect(self.handle, name)

        # set some initial parameters
        # self.FrameCount.setValue(1) #only for fixed mode?
        self.CycleMode.setString("Continuous")
        self.SimplePreAmpGainControl.setString("11-bit (low noise)")
        self.PixelEncoding.setString("Mono12Packed")  # Mono12Packed Mono16

        # Camera object properties
        self.FrameRate.setValue(self.FrameRate.max())
        self.name = (
            "Andor " + self.CameraModel.getValue() + " " + self.SerialNumber.getValue()
        )
        print(self.name)

    def close(self):
        """This method closes the Camera handle.
        """
        SDK3.Close(self.handle)

    def __exit__(self, type_, value, cb):
        """Context manager exit method.
        """
        super(Andor_Camera, self).__exit__(type_, value, cb)
        self.close()

    def set_exposure_time(self, seconds):
        """This method sets the camera exposure time

        :param seconds: exposure in seconds
        :type seconds: float

        """
        self.ExposureTime.setValue(seconds)

    def get_exposure_time(self):
        """This method returns the exposure time in seconds
        """
        return self.ExposureTime.getValue()

    def acquisition_oneshot(self, timeout=1.0):
        """Concrete implementation of :meth:`pymanip.video.Camera.acquisition_oneshot` for the Andor camera.
        """

        # Make sure no acquisition is running & flush
        if self.CameraAcquiring.getValue():
            self.AcquisitionStop()
        SDK3.Flush(self.handle)
        self.MetadataEnable.setValue(True)
        pc_clock = time.time()
        timestamp_clock = self.TimestampClock.getValue()
        timestamp_frequency = self.TimestampClockFrequency.getValue()

        # Init buffer & queue
        bufSize = self.ImageSizeBytes.getValue()
        buf = np.empty(bufSize, "uint8")
        SDK3.QueueBuffer(
            self.handle, buf.ctypes.data_as(SDK3.POINTER(SDK3.AT_U8)), buf.nbytes
        )

        # Start acquisition
        self.AcquisitionStart()
        print("Start acquisition at framerate:", self.FrameRate.getValue())

        try:
            # Wait for buffer
            exposure_ms = self.ExposureTime.getValue() * 1000
            framerate_ms = 1000 / self.FrameRate.getValue()
            timeout_ms = int(max((2 * exposure_ms, 2 * framerate_ms, 1000)))

            pData, lData = SDK3.WaitBuffer(self.handle, timeout_ms)

            # Convert buffer into numpy image
            rbuf, cbuf = self.AOIWidth.getValue(), self.AOIHeight.getValue()
            img = np.empty((rbuf, cbuf), np.uint16)
            xs, ys = img.shape[:2]
            a_s = self.AOIStride.getValue()
            dt = self.PixelEncoding.getString()
            ticks = parse_metadata(buf)
            ts = (ticks - timestamp_clock) / timestamp_frequency + pc_clock
            SDK3.ConvertBuffer(
                buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                img.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                xs,
                ys,
                a_s,
                dt,
                "Mono16",
            )
        finally:
            self.AcquisitionStop()

        return MetadataArray(
            img.reshape((cbuf, rbuf), order="C"), metadata={"timestamp": ts}
        )

    async def acquisition_async(
        self,
        num=np.inf,
        timeout=None,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
    ):
        """Concrete implementation of :meth:`pymanip.video.Camera.acquisition_async` for the Andor camera.

        .. todo::
            add support for initialising_cams
        """

        loop = asyncio.get_event_loop()

        # Make sure no acquisition is running & flush
        if self.CameraAcquiring.getValue():
            self.AcquisitionStop()
        SDK3.Flush(self.handle)
        self.buffer_queued = False

        # Set acquisition mode
        self.CycleMode.setString("Continuous")
        # self.FrameRate.setValue(float(framerate))
        self.MetadataEnable.setValue(True)
        pc_clock = time.time()
        timestamp_clock = self.TimestampClock.getValue()
        timestamp_frequency = self.TimestampClockFrequency.getValue()
        print("ts clock =", timestamp_clock)
        print("ts freq =", timestamp_frequency)

        # Init buffers
        bufSize = self.ImageSizeBytes.getValue()
        buf = np.empty(bufSize, "uint8")
        rbuf, cbuf = self.AOIWidth.getValue(), self.AOIHeight.getValue()
        img = np.empty((rbuf, cbuf), np.uint16)
        xs, ys = img.shape[:2]
        a_s = self.AOIStride.getValue()
        dt = self.PixelEncoding.getString()
        print("Original pixel encoding:", dt)

        # Start acquisition
        self.AcquisitionStart()
        print("Started acquisition at framerate:", self.FrameRate.getValue())
        print("Exposure time is {:.1f} ms".format(self.ExposureTime.getValue() * 1000))
        if timeout is None:
            exposure_ms = self.ExposureTime.getValue() * 1000
            framerate_ms = 1000 / self.FrameRate.getValue()
            timeout_ms = int(max((2 * exposure_ms, 2 * framerate_ms, 1000)))
            timeout = timeout_ms

        try:
            count = 0
            while count < num:
                if not self.buffer_queued:
                    SDK3.QueueBuffer(
                        self.handle,
                        buf.ctypes.data_as(SDK3.POINTER(SDK3.AT_U8)),
                        buf.nbytes,
                    )
                    self.buffer_queued = True
                try:
                    pData, lData = await loop.run_in_executor(
                        None, SDK3.WaitBuffer, self.handle, timeout
                    )
                except Exception:
                    if raise_on_timeout:
                        raise CameraTimeout()
                    else:
                        stop_signal = yield None
                        if stop_signal:
                            break
                        else:
                            continue
                # Convert buffer and yield image
                SDK3.ConvertBuffer(
                    buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                    img.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                    xs,
                    ys,
                    a_s,
                    dt,
                    "Mono16",
                )
                ticks = parse_metadata(buf)
                ts = (ticks - timestamp_clock) / timestamp_frequency + pc_clock
                # if count == 5:
                #    print('image min max:', np.min(img), np.max(img))
                # if count < 10:
                #    print('FPGA ticks =', ticks)
                #    print('Timestamp =', ts)
                self.buffer_queued = False
                stop_signal = yield MetadataArray(
                    img.reshape((cbuf, rbuf), order="C"),
                    metadata={"counter": count, "timestamp": ts},
                )
                count = count + 1
                if stop_signal:
                    break

        finally:
            self.AcquisitionStop()
        if stop_signal:
            yield True


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    with Andor_Camera() as ac:
        ac.set_exposure_time(1e-3)
        img = ac.acquisition_oneshot()
    plt.figure()
    plt.imshow(img, cmap="gray")
    plt.show()
