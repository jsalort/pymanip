"""Asynchronous acquisition session (:mod:`pymanip.video.session`)
==================================================================

.. autoclass:: VideoSession
   :members:
   :private-members:
   :show-inheritance:

"""

import asyncio
from queue import SimpleQueue
from pathlib import Path
from datetime import datetime

import numpy as np
from progressbar import ProgressBar
import cv2

from pymanip.asyncsession import AsyncSession


class VideoSession(AsyncSession):
    """This class represents a video acquisition session.
    """

    def __init__(
        self,
        camera_or_camera_list,
        trigger_gbf,
        framerate,
        nframes,
        output_format,
        output_path=None,
        exist_ok=False,
    ):
        if isinstance(camera_or_camera_list, (list, tuple)):
            self.camera_list = camera_or_camera_list
        else:
            self.camera_list = (camera_or_camera_list,)
        self.trigger_gbf = trigger_gbf
        self.framerate = framerate
        self.nframes = nframes
        if output_format not in ("png", "tif", "mp4", "jpg"):
            raise ValueError("output_format must be png, tif, jpg or mp4")
        self.output_format = output_format

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
            cam.set_trigger_mode(True)
        self.image_queues = [SimpleQueue() for _ in self.camera_list]
        self.acquisition_finished = [False] * len(self.camera_list)
        self.initialising_cams = set(self.camera_list)

    async def _acquire_images(self, cam_no):
        with self.camera_list[cam_no] as cam:
            if hasattr(self, "prepare_camera"):
                self.prepare_camera(cam)
            if cam_no == 0:
                pb = ProgressBar(initial_value=0, min_value=0, max_value=self.nframes)
            gen = cam.acquisition_async(
                self.nframes,
                initialising_cams=self.initialising_cams,
                raise_on_timeout=False,
            )
            n = 0
            async for im in gen:
                if im is not None:
                    self.image_queues[cam_no].put(im)
                    n = n + 1
                    if cam_no == 0:
                        pb.update(n)
                else:
                    print("Camera timed out! Stopping...")
                    self.running = False
                if not self.running:
                    success = await gen.asend(True)
                    if not success:
                        print("Unable to stop camera acquisition")
            if cam_no == 0:
                pb.finish()
            self.acquisition_finished[cam_no] = True
            if all(self.acquisition_finished):
                self.running = False

    async def _start_clock(self):
        while len(self.initialising_cams) > 0:
            await asyncio.sleep(0.1)
        with self.trigger_gbf:
            self.trigger_gbf.trigger()
        return datetime.now().timestamp()

    async def _save_images(self):
        loop = asyncio.get_event_loop()
        i = [0] * len(self.camera_list)
        pb = None

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
                    if hasattr(self, "process_image"):
                        img = await loop.run_in_executor(None, self.process_image, img)
                    filepath = (
                        self.output_folder
                        / f"img-cam{cam_no:d}-{(i[cam_no]+1):04d}.{self.output_format:}"
                    )
                    await loop.run_in_executor(
                        None, cv2.imwrite, str(filepath), img, None
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

    async def _save_video(self, cam_no, gain=1.0):
        loop = asyncio.get_event_loop()
        command = None
        fmin = None
        fmax = None
        while True:
            if not self.running:
                if all([q.empty() for q in self.image_queues]):
                    break
            if self.image_queues[cam_no].empty():
                await asyncio.sleep(0.1)
            else:
                img = self.image_queues[cam_no].get()
                if hasattr(self, "process_image"):
                    img = await loop.run_in_executor(None, self.process_image, img)
                if command is None:
                    output_size = img.shape
                    command = [
                        "ffmpeg",
                        "-y",
                        "-f",
                        "rawvideo",
                        "-vcodec",
                        "rawvideo",
                        "-s",
                        "{}x{}".format(*output_size),
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

                fff = (
                    255 * gain * np.array(img - fmin, dtype=np.float64) / (fmax - fmin)
                )
                fff[fff < 0] = 0
                fff[fff > 255] = 255
                ff = np.array(fff, dtype=np.uint8)
                if self.camera_list[cam_no].color_order == "RGB":
                    ff = cv2.cvtColor(ff, cv2.COLOR_RGB2BGR)
                # ff = cv2.resize(np.array(fff, dtype=np.uint8), output_size)
                await proc.communicate(ff.tostring())

    async def main(self):
        with self.trigger_gbf:
            self.trigger_gbf.configure_burst(self.framerate, self.nframes)
            self.save_parameter(fps=self.framerate, num_imgs=self.nframes)
        acquisition_tasks = [
            self._acquire_images(cam_no) for cam_no in range(len(self.camera_list))
        ]
        clock_task = self._start_clock()
        if self.output_format == "mp4":
            save_tasks = [
                self._save_video(cam_no) for cam_no in range(len(self.camera_list))
            ]
        else:
            save_tasks = [self._save_images()]
        await self.monitor(
            *acquisition_tasks, clock_task, *save_tasks, server_port=None
        )
        _, camera_timestamps = self.logged_variable("ts")
        _, camera_counter = self.logged_variable("count")

        dt = camera_timestamps[1:] - camera_timestamps[:-1]
        mean_dt = np.mean(dt)
        mean_fps = 1.0 / mean_dt
        min_dt = np.min(dt)
        max_dt = np.max(dt)
        min_fps = 1.0 / max_dt
        max_fps = 1.0 / min_dt
        print(f"fps = {mean_fps:.3f} (between {min_fps:.3f} and {max_fps:.3f})")

        return camera_timestamps, camera_counter

    def run(self):
        ts, count = asyncio.run(self.main())
        return ts, count
