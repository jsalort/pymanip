"""Photometrics Camera module (:mod:`pymanip.video.photometrics.camera`)
========================================================================

This module implements the :class:`pymanip.video.photometrics.Photometrics_Camera` using the
`Python wrapper provided by Photometrics <https://github.com/Photometrics/PyVCAM>`_.
The documentation for the PVCAM SDK is available `online <https://www.photometrics.com/docs/pvcam-sdk/>`_.

.. autoclass:: Photometrics_Camera
   :members:
   :private-members:
   :show-inheritance:

"""

from time import monotonic
import asyncio
import numpy as np
from pymanip.video import MetadataArray, Camera, CameraTimeout

from pyvcam import pvc
from pyvcam.camera import Camera as PVCamera

pvc_initialized = False


class Photometrics_Camera(Camera):
    """Concrete :class:`pymanip.video.Camera` class for Photometrics camera."""

    def __init__(self, cam_num=0, readout_port=0):
        """Constructor method.

        readout_port is camera mode:
            - readout_port = 0 ("Sensitivity") 12 bits, max fps = 88
            - readout_port = 1 ("Speed") 8 bits, max fps = 100
            - readout_port = 2 ("Dynamic Range") 16 bits, max fps = 83
        """
        global pvc_initialized

        if not pvc_initialized:
            print("pvc.init_pvcam")
            pvc.init_pvcam()
            pvc_initialized = True

        for num, cam in enumerate(PVCamera.detect_camera()):
            if num == cam_num:
                break
        else:
            raise (f"Unable to find camera num {cam_num:}.")
        self.cam = cam
        self.cam.open()
        self.cam.readout_port = readout_port

        self.cam.meta_data_enabled = True
        print(self.cam.name)

    def close(self):
        """Close connection to the camera"""
        self.cam.close()
        self.cam = None

    def __exit__(self, type_, value, cb):
        """Context manager exit method"""
        super().__exit__(type_, value, cb)
        self.close()

    @property
    def name(self):
        return self.cam.name

    def set_trigger_mode(self, external):
        """Set external trigger (edge rising).
        Possible modes are available in self.cam.exp_modes.
        """
        if external:
            self.cam.exp_mode = "Edge Trigger"
        else:
            self.cam.exp_mode = "Internal Trigger"

    def get_trigger_mode(self):
        if self.cam.exp_mode == "Internal Trigger":
            return False
        return True

    def set_exposure_time(self, seconds):
        """This method sets the exposure time for the camera.

        :param seconds: exposure in seconds.
        :type seconds: float
        """
        self.cam.exp_time = int(seconds * 1e3)
        print("Exposure time set to", 1000 * seconds, "ms")

    def get_exposure_time(self):
        """This method gets the exposure time in seconds for the camera."""
        return self.cam.exp_time / 1e3

    def set_roi(self, roiX0=0, roiY0=0, roiX1=0, roiY1=0):
        """This method sets the positions of the upper left corner (X0,Y0) and lower right
        (X1,Y1) corner of the ROI (region of interest) in pixels.
        """
        self.cam.roi = (roiX0, roiY0, roiX1, roiY1)

    async def get_image(self, loop, timeout):
        start_time = monotonic()
        while monotonic() - start_time < timeout:
            frameStatus = self.cam.check_frame_status()
            if frameStatus == "READOUT_FAILED":
                raise RuntimeError("Readout failed")
            else:
                future = loop.run_in_executor(
                    None,
                    pvc.get_frame,
                    self.cam._Camera__handle,
                    self.cam._Camera__shape[0],
                    self.cam._Camera__shape[1],
                    self.cam._Camera__bits_per_pixel,
                )
                try:
                    frame, fps, frame_count = await asyncio.wait_for(
                        future, timeout=timeout, loop=loop
                    )
                except asyncio.TimeoutError:
                    print("Timeout while waiting for poll_frame")
                    break
                return (
                    frame.reshape(
                        self.cam._Camera__shape[1], self.cam._Camera__shape[0]
                    ),
                    fps,
                    frame_count,
                )

        print(
            "Out of the loop after",
            monotonic() - start_time,
            "second with frame status",
            frameStatus,
        )
        raise CameraTimeout

    async def acquisition_async(
        self,
        num=np.inf,
        timeout=None,
        raw=False,
        initialising_cams=None,
        raise_on_timeout=True,
    ):
        """Concrete implementation of :meth:`pymanip.video.Camera.acquisition_async` for the Photometrics camera.

        timeout in milliseconds.
        """
        loop = asyncio.get_event_loop()
        if timeout is None:
            timeout = max((5000, 5 * self.get_exposure_time() * 1000))
        try:
            count = 0
            """
            if np.isfinite(num):
                self.cam.start_seq(num_frames=num)
            else:
                self.cam.start_live()
            """
            self.cam.start_live()
            while count < num:
                if (
                    count == 0
                    and initialising_cams is not None
                    and self in initialising_cams
                ):
                    initialising_cams.remove(self)
                try:
                    frame, fps, frame_count = await self.get_image(loop, timeout / 1000)
                except CameraTimeout:
                    print("Camera timeout")
                    if raise_on_timeout:
                        raise
                    else:
                        stop_signal = yield None
                        if stop_signal:
                            break
                        else:
                            continue
                # d'après la doc, timestampBOF*timestampResN est en nanoseconds
                # mais il n'y a pas timestampResN, et il semble que c'est plutôt en picoseconds ?
                stop_signal = yield MetadataArray(
                    frame["pixel_data"],  # no copy
                    metadata={
                        "counter": frame_count,
                        "timestamp": frame["meta_data"]["frame_header"]["timestampBOF"]
                        / 1e12,
                    },
                )
                if count == 0:
                    for k, v in frame["meta_data"]["frame_header"].items():
                        print(k, v)
                    print("roi_headers", frame["meta_data"]["roi_headers"])
                count += 1
                if stop_signal:
                    break
        finally:
            self.cam.finish()
        if stop_signal:
            yield True


if __name__ == "__main__":
    with Photometrics_Camera() as cam:
        print("Exposure =", cam.get_exposure_time())
