"""Asynchronous acquisition session (:mod:`pymanip.video.session`)
==================================================================

This module provides a high-level class, :class:`VideoSession`, to be used in acquisition scripts.
Users should subclass :class:`VideoSession`, and add two methods: ``prepare_camera(self, cam)`` in which
additionnal camera setup may be done, and ``process_image(self, img)`` in which possible image post-processing
can be done.
The ``prepare_camera`` method, if defined, is called before starting camera acquisition.
The ``process_image`` method, if defined, is called before saving the image.

The implementation allows simultaneous acquisition of several cameras, trigged by a function generator.
Concurrent tasks are set up to grab images from the cameras to RAM memory, while a background task saves
the images to the disk. The cameras, and the trigger, are released as soon as acquisition is finished, even if the images are
still being written to the disk, which allows several scripts to be executed concurrently (if the host computer
has enough RAM). The ``trigger_gbf`` object must implement ``configure_square()`` and ``configure_burst()`` methods
to configure square waves and bursts, as well as ``trigger()`` method for software trigger. An exemple is
:class:`fluidlab.instruments.funcgen.agilent_33220a.Agilent33220a`.

A context manager must be used to ensure proper saving of the metadata to the database.

**Example**

.. code:: python

   import numpy as np
   import cv2

   from pymanip.video.session import VideoSession
   from pymanip.video.ximea import Ximea_Camera
   from pymanip.instruments import Agilent33220a


   class TLCSession(VideoSession):

       def prepare_camera(self, cam):
           # Set up camera (keep values as custom instance attributes)
           self.exposure_time = 50e-3
           self.decimation_factor = 2

           cam.set_exposure_time(self.exposure_time)
           cam.set_auto_white_balance(False)
           cam.set_limit_bandwidth(False)
           cam.set_vertical_skipping(self.decimation_factor)
           cam.set_roi(1298, 1833, 2961, 2304)

           # Save some metadata to the AsyncSession underlying database
           self.save_parameter(
               exposure_time=self.exposure_time,
               decimation_factor=self.decimation_factor,
           )

       def process_image(self, img):
           # On decimate manuellement dans la direction horizontale
           img = img[:, ::self.decimation_factor, :]

           # On redivise encore tout par 2
           # image_size = (img.shape[0]//2, img.shape[1]//2)
           # img = cv2.resize(img, image_size)

           # Correction (fixe) de la balance des blancs
           kR = 1.75
           kG = 1.0
           kB = 2.25
           b, g, r = cv2.split(img)
           img = np.array(
               cv2.merge([kB*b, kG*g, kR*r]),
               dtype=img.dtype,
           )

           # Rotation de 180°
           img = cv2.rotate(img, cv2.ROTATE_180)

           return img


   with TLCSession(
       Ximea_Camera(),
       trigger_gbf=Agilent33220a("USB0::0x0957::0x0407::SG43000299::INSTR"),
       framerate=24,
       nframes=1000,
       output_format="png",
       ) as sesn:

       # ROI helper (remove cam.set_roi in prepare_camera for correct usage)
       # sesn.roi_finder()

       # Single picture test
       # sesn.show_one_image()

       # Live preview
       # ts, count = sesn.live()

       # Run actual acquisition
       ts, count = sesn.run(additionnal_trig=1)

.. autoclass:: VideoSession
   :members:
   :private-members:
   :show-inheritance:

"""

import asyncio
from queue import SimpleQueue
from pathlib import Path
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
from progressbar import ProgressBar
import cv2

from pymanip.asyncsession import AsyncSession
from pymanip.video import MetadataArray


class VideoSession(AsyncSession):
    """This class represents a video acquisition session.

    :param camera_or_camera_list: Camera(s) to be acquired
    :type camera_or_camera_list: :class:`~pymanip.video.Camera` or list of :class:`~pymanip.video.Camera`
    :param trigger_gbf: function generator to be used as trigger
    :type trigger_gbf: :class:`~fluidlab.instruments.drivers.Driver`
    :param framerate: desired framerate
    :type framerate: float
    :param nframes: desired number of frames
    :type nframes: int
    :param output_format: desired output image format, "bmp", "png", tif", or video format "mp4"
    :type output_format: str
    :param output_format_params: additionnal params to be passed to :func:`cv2.imwrite`
    :type output_format_params: list
    :param exist_ok: allows to override existing output folder
    :type exist_ok: bool

    """

    def __init__(
        self,
        camera_or_camera_list,
        trigger_gbf,
        framerate,
        nframes,
        output_format,
        output_format_params=None,
        output_path=None,
        exist_ok=False,
        timeout=None,
        burst_mode=True,
    ):
        """Constructor method"""
        if isinstance(camera_or_camera_list, (list, tuple)):
            self.camera_list = camera_or_camera_list
        else:
            self.camera_list = (camera_or_camera_list,)
        self.trigger_gbf = trigger_gbf
        self.framerate = framerate
        self.nframes = nframes
        if output_format not in ("png", "tif", "mp4", "jpg", "bmp"):
            raise ValueError("output_format must be png, tif, jpg, bmp, or mp4")
        self.output_format = output_format
        self.output_format_params = output_format_params
        self.timeout = timeout
        self.burst_mode = burst_mode
        
        if output_path is None:
            current_date = datetime.today().strftime("%Y-%m-%d")
            base_dir = Path(".") / current_date
            base_dir.mkdir(exist_ok=True)

        if output_format == "mp4":
            if output_path is None:
                i = 1
                while True:
                    self.output_paths = [
                        base_dir / f"{i:02d}-cam{no:}.mp4"
                        for no in range(len(self.camera_list))
                    ]
                    session_name = base_dir / f"{i:02d}"
                    for ff in self.output_paths:
                        if ff.exists():
                            i = i + 1
                            break
                    else:
                        break
            else:
                self.output_paths = [
                    Path(output_path + f"-cam{no:}.mp4")
                    for no in range(len(self.camera_list))
                ]
                for ff in self.output_file:
                    if self.output_file.exists():
                        if exist_ok:
                            self.output_file.unlink()
                        else:
                            raise RuntimeError(
                                f"The file {self.output_file:} already exists."
                            )
                session_name = str(self.output_file)
                if session_name.endswith(".mp4"):
                    session_name = session_name[:-4]
            if len(self.output_paths) == 1:
                print("Output file is", self.output_paths[0])
            else:
                print("Output files are")
                for ff in self.output_paths:
                    print(str(ff))
        else:
            if output_path is None:
                i = 1
                while True:
                    self.output_folder = base_dir / f"{i:02d}"
                    session_name = self.output_folder / "session"
                    if self.output_folder.exists():
                        i = i + 1
                    else:
                        self.output_folder.mkdir()
                        break
            else:
                self.output_folder = Path(output_path)
                self.output_folder.mkdir(exist_ok=exist_ok)
                session_name = self.output_folder
            print("Output folder is", str(self.output_folder.absolute()))

        super().__init__(session_name, delay_save=True)
        for cam in self.camera_list:
            if self.trigger_gbf is not None or self.trigger_gbf is True:
                cam.set_trigger_mode(True)
            else:
                cam.set_trigger_mode(False)
                cam.set_frame_rate(framerate)
        if self.trigger_gbf is True:
            self.trigger_gbf = None
        self.image_queues = [SimpleQueue() for _ in self.camera_list]
        self.acquisition_finished = [False] * len(self.camera_list)
        self.initialising_cams = set(self.camera_list)

    async def _acquire_images(self, cam_no):
        """Private instance method: image acquisition task.
        This task asynchronously iterates over the given camera frames, and puts the obtained images
        in a simple FIFO queue.

        :param cam_no: camera index
        :type cam_no: int
        """
        with self.camera_list[cam_no] as cam:
            if hasattr(self, "prepare_camera"):
                self.prepare_camera(cam)
            if cam_no == 0 and np.isfinite(self.nframes):
                pb = ProgressBar(initial_value=0, min_value=0, max_value=self.nframes)
            else:
                pb = None
            gen = cam.acquisition_async(
                self.nframes,
                initialising_cams=self.initialising_cams,
                raise_on_timeout=False,
                timeout=self.timeout,
            )
            n = 0
            async for im in gen:
                if im is not None:
                    self.image_queues[cam_no].put(im.copy())
                    n = n + 1
                    if pb is not None:
                        pb.update(n)
                else:
                    print("Camera timed out! Stopping...")
                    self.running = False
                if not self.running:
                    success = await gen.asend(True)
                    if not success:
                        print("Unable to stop camera acquisition")
            if pb is not None:
                pb.finish()
            self.acquisition_finished[cam_no] = True
            if all(self.acquisition_finished):
                self.running = False
        print(f"{n:d} images acquired (cam {cam_no:}).")

    async def _start_clock(self):
        """Private instance method: clock starting task.
        This task waits for all the cameras to be ready for trigger, and then sends a software trig to
        the function generator.
        """
        print("clock task")
        while len(self.initialising_cams) > 0:
            await asyncio.sleep(0.1)
        with self.trigger_gbf:
            self.trigger_gbf.trigger()
            print("trigger sent")
        return datetime.now().timestamp()

    async def _save_images(self, keep_in_RAM=False, unprocessed=False, no_save=False):
        """Private instance method: image saving task.
        This task checks the image FIFO queue. If an image is available, it is taken out of the queue and
        saved to the disk.

        :param keep_in_RAM: if set, images are not saved and kept in a list.
        :type keep_in_RAM: bool
        :param unprocessed: if set, the ``process_image`` method is not called.
        :type unprocessed: bool
        :param no_save: do not actually save (dry run), for testing purposes
        :type no_save: bool
        """
        loop = asyncio.get_event_loop()
        i = [0] * len(self.camera_list)
        pb = None

        if keep_in_RAM:
            self.image_list = [list() for _ in range(len(self.camera_list))]

        while True:
            if not self.running:
                if all([q.empty() for q in self.image_queues]):
                    break
            for cam_no, q in enumerate(self.image_queues):
                if q.empty():
                    await asyncio.sleep(0.1)
                else:
                    img = q.get()
                    self.add_entry(
                        ts=img.metadata["timestamp"], count=img.metadata["counter"]
                    )
                    if not no_save:
                        if hasattr(self, "process_image") and not unprocessed:
                            img = await loop.run_in_executor(None, self.process_image, img)
                        filepath = (
                            self.output_folder
                            / f"img-cam{cam_no:d}-{(i[cam_no]+1):04d}.{self.output_format:}"
                        )
                    if keep_in_RAM:
                        self.image_list[cam_no].append(img)
                    elif not no_save:
                        await loop.run_in_executor(
                            None,
                            cv2.imwrite,
                            str(filepath),
                            img,
                            self.output_format_params,
                        )
                    i[cam_no] += 1
            if not self.running:
                i_min = min(i)
                if pb is None:
                    print("Saving is continuing...")
                    pb = ProgressBar(
                        min_value=0, max_value=self.nframes, initial_value=i_min
                    )
                else:
                    pb.update(i_min)
        if pb is not None:
            pb.finish()
        for cam_no, ii in enumerate(i):
            print(f"{ii:d} images saved (cam {cam_no:}).")

    def _convert_for_ffmpeg(self, cam_no, img, fmin, fmax, gain):
        """Private instance method: image conversion for ffmpeg process.
        This method prepares the input image to bytes to be sent to the ffmpeg pipe.

        :param cam_no: camera index
        :type cam_no: int
        :param img: image to process
        :type img: :class:`numpy.ndarray`
        :param fmin: minimum level
        :type fmin: int
        :param fmax: maximum level
        :type fmax: int
        :param gain: gain
        :type gain: float
        """
        fff = 255 * gain * np.array(img - fmin, dtype=np.float64) / (fmax - fmin)
        fff[fff < 0] = 0
        fff[fff > 255] = 255
        ff = np.array(fff, dtype=np.uint8)
        if self.camera_list[cam_no].color_order == "RGB":
            ff = cv2.cvtColor(ff, cv2.COLOR_RGB2BGR)
        return ff.tostring()

    async def _save_video(self, cam_no, gain=1.0, unprocessed=False):
        """Private instance method: video saving task.
        This task waits for images in the FIFO queue, and sends them to ffmpeg via a pipe.

        :param cam_no: camera index
        :type cam_no: int
        :param gain: gain
        :type gain: float
        :param unprocessed: if set, :meth:`process_image` method is not called
        :type unprocessed: bool
        """
        loop = asyncio.get_event_loop()
        command = None
        fmin = None
        fmax = None
        while self.running or not self.image_queues[cam_no].empty():
            if self.image_queues[cam_no].empty():
                await asyncio.sleep(0.1)
            else:
                img = self.image_queues[cam_no].get()
                self.add_entry(
                    ts=img.metadata["timestamp"], count=img.metadata["counter"]
                )
                if hasattr(self, "process_image") and not unprocessed:
                    img = await loop.run_in_executor(None, self.process_image, img)
                if command is None:
                    output_size = img.shape
                    command = [
                        "-y",
                        "-f",
                        "rawvideo",
                        "-vcodec",
                        "rawvideo",
                        "-s",
                        "{}x{}".format(output_size[1], output_size[0]),
                        "-pix_fmt",
                        "bgr24",
                        "-r",
                        str(self.framerate),
                        "-i",
                        "-",
                        "-an",
                        "-vcodec",
                        "mpeg4",
                        "-b:v",
                        "5000k",
                        str(self.output_paths[cam_no]),
                    ]
                    proc = await asyncio.create_subprocess_exec(
                        "ffmpeg",
                        *command,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=None,
                        stderr=None,
                    )
                if fmin is None:
                    fmin = np.min(img)
                if fmax is None:
                    fmax = np.max(img)
                data = await loop.run_in_executor(
                    None, self._convert_for_ffmpeg, cam_no, img, fmin, fmax, gain
                )
                proc.stdin.write(data)
                await proc.stdin.drain()
        proc.stdin.close()
        await asyncio.wait_for(proc.stdin.wait_closed(), timeout=5.0)
        await asyncio.wait_for(proc.wait(), timeout=5.0)
        print("ffmpeg has terminated.")

    async def _fast_acquisition_to_ram(self, cam_no, total_timeout_s):
        """Private instance method: fast acquisition to ram task"""
        with self.camera_list[cam_no] as cam:
            if hasattr(self, "prepare_camera"):
                self.prepare_camera(cam)
            ts, count, images = await cam.fast_acquisition_to_ram(
                self.nframes,
                total_timeout_s,
                self.initialising_cams,
                False,  # raise_on_timeout
            )
        return ts, count, images

    async def main(
        self,
        keep_in_RAM=False,
        additionnal_trig=0,
        live=False,
        unprocessed=False,
        delay_save=False,
        no_save=False,
    ):
        """Main entry point for acquisition tasks. This asynchronous task can be called
        with :func:`asyncio.run`, or combined with other user-defined tasks.

        :param keep_in_RAM: do not save to disk, but keep images in a list
        :type keep_in_RAM: bool
        :param additionnal_trig: additionnal number of pulses sent to the camera
        :type additionnal_trig: int
        :param live: toggle live preview
        :type live: bool
        :param unprocessed: do not call :meth:`process_image` method.
        :type unprocessed: bool
        :return: camera_timestamps, camera_counter
        :rtype: :class:`numpy.ndarray`, :class:`numpy.ndarray`
        """
        if self.trigger_gbf is not None:
            with self.trigger_gbf:
                if live or self.nframes < 2 or not self.burst_mode:
                    self.trigger_gbf.configure_square(0.0, 5.0, freq=self.framerate)
                else:
                    self.trigger_gbf.configure_burst(
                        self.framerate, self.nframes + additionnal_trig
                    )
                    self.save_parameter(fps=self.framerate, num_imgs=self.nframes)

        if delay_save and all(
            [
                hasattr(self.camera_list[cam_no], "fast_acquisition_to_ram")
                for cam_no in range(len(self.camera_list))
            ]
        ):
            if live:
                raise ValueError("delay_save and live are not compatible")
            print("Acquisition in fast mode to RAM")

            # Acquisition to RAM
            total_timeout_s = 5 + (self.nframes / self.framerate)
            acquisition_tasks = [
                self._fast_acquisition_to_ram(cam_no, total_timeout_s)
                for cam_no in range(len(self.camera_list))
            ]
            dt_start = datetime.now()
            dt_end = dt_start + timedelta(seconds=total_timeout_s)
            print("Acquisition start time:", dt_start.strftime("%d-%m-%Y %H:%M:%S"))
            print("              end time:", dt_end.strftime("%d-%m-%Y %H:%M:%S"))
            results = await asyncio.gather(*acquisition_tasks, self._start_clock())
            self.running = False

            # Convert from lists to queues (no data copy involved)
            for cam_no, (ts_all, count_all, images_all) in zip(
                range(len(self.camera_list)), results
            ):
                for ts, count, image in zip(ts_all, count_all, images_all):
                    self.image_queues[cam_no].put(
                        MetadataArray(
                            image,
                            metadata={
                                "counter": count,
                                "timestamp": ts,
                            },
                        )
                    )
        else:
            acquisition_tasks = [
                self._acquire_images(cam_no) for cam_no in range(len(self.camera_list))
            ]
            if live:
                save_tasks = [self._live_preview(unprocessed)]
            elif self.output_format == "mp4":
                save_tasks = [self._start_clock()]
                if not delay_save:
                    save_tasks = save_tasks + [
                        self._save_video(cam_no, unprocessed=unprocessed)
                        for cam_no in range(len(self.camera_list))
                    ]

            else:
                if self.trigger_gbf is not None:
                    save_tasks = [self._start_clock()]
                else:
                    save_tasks = []
                if not delay_save:
                    save_tasks = save_tasks + [
                        self._save_images(keep_in_RAM, unprocessed)
                    ]

            await self.monitor(*acquisition_tasks, *save_tasks, server_port=None)

        # Post-acquisition save if the save_tasks were not included (in fast mode, or in regular mode)
        if delay_save:
            if self.output_format == "mp4":
                for cam_no in range(len(self.camera_list)):
                    await self._save_video(cam_no, unprocessed=unprocessed)
            else:
                await self._save_images(keep_in_RAM, unprocessed, no_save)

        # Post-acquisition information
        _, camera_timestamps = self.logged_variable("ts")
        _, camera_counter = self.logged_variable("count")
        
        if isinstance(camera_timestamps[0], str):
            camera_timestamps = np.array([datetime.fromisoformat(ts).timestamp() for ts in camera_timestamps])

        if camera_timestamps.size > 2:
            dt = camera_timestamps[1:] - camera_timestamps[:-1]
            mean_dt = np.mean(dt)
            mean_fps = 1.0 / mean_dt
            min_dt = np.min(dt)
            max_dt = np.max(dt)
            min_fps = 1.0 / max_dt
            max_fps = 1.0 / min_dt
            print(f"fps = {mean_fps:.3f} (between {min_fps:.3f} and {max_fps:.3f})")

        return camera_timestamps, camera_counter

    def run(self, additionnal_trig=0, delay_save=False, no_save=False):
        """Run the acquisition.

        :param additionnal_trig: additionnal number of pulses sent to the camera
        :type additionnal_trig: int
        :return: camera_timestamps, camera_counter
        :rtype: :class:`numpy.ndarray`, :class:`numpy.ndarray`
        """
        ts, count = asyncio.run(
            self.main(additionnal_trig=additionnal_trig, delay_save=delay_save, no_save=no_save)
        )
        return ts, count

    def live(self):
        """Starts live preview."""
        old_nframes = self.nframes
        old_output_format = self.output_format
        try:
            self.nframes = float("inf")
            self.output_format = "png"
            ts, count = asyncio.run(self.main(live=True))
        finally:
            self.nframes = old_nframes
            self.output_format = old_output_format
        return ts, count

    def get_one_image(
        self, additionnal_trig=0, unprocessed=False, unpack_solo_cam=True
    ):
        """Get one image from the camera(s).

        :param additionnal_trig: additionnal number of pulses sent to the camera
        :type additionnal_trig: int
        :param unprocessed: do not call :meth:`process_image` method.
        :type unprocessed: bool
        :param unpack_solo_cam: if set, keep list on return, even if there is only one camera
        :type unpack_solo_cam: bool
        :return: image(s) from the camera(s)
        :rtype: :class:`numpy.ndarray` or list of :class:`numpy.ndarray` (if multiple cameras, or ``unpack_solo_cam=False``).
        """
        old_nframes = self.nframes
        old_output_format = self.output_format
        try:
            self.nframes = 1
            self.output_format = "png"
            ts, count = asyncio.run(
                self.main(
                    keep_in_RAM=True,
                    additionnal_trig=additionnal_trig,
                    unprocessed=unprocessed,
                )
            )
            if len(self.camera_list) > 1 or not unpack_solo_cam:
                result = [im[0] for im in self.image_list]
            else:
                result = self.image_list[0][0]
        finally:
            self.nframes = old_nframes
            self.output_format = old_output_format
        return result

    def show_one_image(self, additionnal_trig=0):
        """Get one image from the camera(s), and plot them with matplotlib.

        :param additionnal_trig: additionnal number of pulses sent to the camera
        :type additionnal_trig: int
        """
        image = self.get_one_image(additionnal_trig)
        if isinstance(image, list):
            for img in image:
                plt.figure()
                if img.ndim == 2:
                    plt.imshow(img)
                    plt.colorbar()
                else:
                    plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        else:
            plt.figure()
            if image.ndim == 2:
                plt.imshow(image)
                plt.colorbar()
            else:
                plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.show()

    def roi_finder(self, additionnal_trig=0):
        """Helper to determine the ROI. This method grabs one unprocessed image from the camera(s),
        and allows interactive selection of the region of interest.
        Attention: it is assumed that the :meth:`prepare_camera` method did not already set the ROI.

        :param additionnal_trig: additionnal number of pulses sent to the camera
        :type additionnal_trig: int
        :return: region of interest coordinates, X0, Y0, X1, Y1
        :rtype: list of floats
        """
        images = self.get_one_image(
            additionnal_trig, unprocessed=True, unpack_solo_cam=False
        )
        for cam_no, img in enumerate(images):
            try:
                l, c = img.shape
                color = False
            except ValueError:
                l, c, ncomp = img.shape
                color = True

            # Convert color order if necessary
            if color and self.camera_list[cam_no].color_order == "BGR":
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            plt.figure()
            plt.imshow(img)
            plt.title("Unprocessed image")
            print("Click on top-left and bottom-right corners")
            bottom_left, top_right = plt.ginput(2)
            X0, Y0 = bottom_left
            X1, Y1 = top_right
            print("ROI is", X0, Y0, X1, Y1)
        return X0, Y0, X1, Y1

    async def _live_preview(self, unprocessed=False):
        """Private instance method: live preview task.
        This task checks the FIFO queue, drains it and shows the last frame of each camera using cv2.
        If more than one frame is in the queues, the older frames are dropped.

        :param unprocessed: do not call :meth:`process_image` method.
        :type unprocessed: bool
        """
        minimum = None
        maximum = None
        while self.running or any([not q.empty() for q in self.image_queues]):
            for cam_no, q in enumerate(self.image_queues):
                ndropped = -1
                img = None
                while not q.empty():
                    img = q.get()
                    self.add_entry(
                        ts=img.metadata["timestamp"], count=img.metadata["counter"]
                    )
                    ndropped += 1
                if img is not None:
                    if ndropped > 0:
                        print(ndropped, "frames dropped.", end="\r")
                    if hasattr(self, "process_image") and not unprocessed:
                        img = self.process_image(img)

                    # Show only a 800x600 window (max)
                    try:
                        l, c = img.shape
                        color = False
                        minimum = np.min(img)
                        maximum = np.max(img)
                        maxint = np.iinfo(img.dtype).max
                    except ValueError:
                        l, c, ncomp = img.shape
                        color = True
                    zoom_l = l / 600
                    zoom_c = c / 800
                    zoom = max([zoom_l, zoom_c])
                    if zoom > 1:
                        img = cv2.resize(img, (int(c / zoom), int(l / zoom)))

                    # Convert color order if necessary
                    if color:
                        if self.camera_list[cam_no].color_order == "RGB":
                            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    else:
                        # if not in color, we rescale min max to first image (otherwise may appear black)
                        img = (maxint // (maximum - minimum)) * (img - minimum)

                    # Show image and run cv2 event loop
                    cv2.imshow(f"cam{cam_no:}", img)
            k = cv2.waitKey(1)
            if k != -1:
                self.ask_exit()
            await asyncio.sleep(0.1)
        cv2.destroyAllWindows()
