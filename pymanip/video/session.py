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
import matplotlib.pyplot as plt
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
        output_format_params=None,
        output_path=None,
        exist_ok=False,
    ):
        """Constructor method
        """
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
            if cam_no == 0 and np.isfinite(self.nframes):
                pb = ProgressBar(initial_value=0, min_value=0, max_value=self.nframes)
            else:
                pb = None
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
        while len(self.initialising_cams) > 0:
            await asyncio.sleep(0.1)
        with self.trigger_gbf:
            self.trigger_gbf.trigger()
        return datetime.now().timestamp()

    async def _save_images(self, keep_in_RAM=False, unprocessed=False):
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
                    if hasattr(self, "process_image") and not unprocessed:
                        img = await loop.run_in_executor(None, self.process_image, img)
                    filepath = (
                        self.output_folder
                        / f"img-cam{cam_no:d}-{(i[cam_no]+1):04d}.{self.output_format:}"
                    )
                    if keep_in_RAM:
                        self.image_list[cam_no].append(img)
                    else:
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
        fff = 255 * gain * np.array(img - fmin, dtype=np.float64) / (fmax - fmin)
        fff[fff < 0] = 0
        fff[fff > 255] = 255
        ff = np.array(fff, dtype=np.uint8)
        if self.camera_list[cam_no].color_order == "RGB":
            ff = cv2.cvtColor(ff, cv2.COLOR_RGB2BGR)
        return ff.tostring()

    async def _save_video(self, cam_no, gain=1.0, unprocessed=False):
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

    async def main(
        self, keep_in_RAM=False, additionnal_trig=0, live=False, unprocessed=False
    ):
        with self.trigger_gbf:
            if live or self.nframes < 2:
                self.trigger_gbf.configure_square(0.0, 5.0, freq=self.framerate)
            else:
                self.trigger_gbf.configure_burst(
                    self.framerate, self.nframes + additionnal_trig
                )
                self.save_parameter(fps=self.framerate, num_imgs=self.nframes)
        acquisition_tasks = [
            self._acquire_images(cam_no) for cam_no in range(len(self.camera_list))
        ]
        if live:
            save_tasks = [self._live_preview(unprocessed)]
        elif self.output_format == "mp4":
            save_tasks = [self._start_clock()] + [
                self._save_video(cam_no, unprocessed=unprocessed)
                for cam_no in range(len(self.camera_list))
            ]
        else:
            save_tasks = [
                self._start_clock(),
                self._save_images(keep_in_RAM, unprocessed),
            ]
        await self.monitor(*acquisition_tasks, *save_tasks, server_port=None)
        _, camera_timestamps = self.logged_variable("ts")
        _, camera_counter = self.logged_variable("count")

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

    def run(self, additionnal_trig=0):
        ts, count = asyncio.run(self.main(additionnal_trig=additionnal_trig))
        return ts, count

    def live(self):
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
        image = self.get_one_image(additionnal_trig)
        if isinstance(image, list):
            for img in image:
                plt.figure()
                plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        else:
            plt.figure()
            plt.imshow(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        plt.show()

    def roi_finder(self, additionnal_trig=0):
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
                    except ValueError:
                        l, c, ncomp = img.shape
                        color = True
                    zoom_l = l / 600
                    zoom_c = c / 800
                    zoom = max([zoom_l, zoom_c])
                    if zoom > 1:
                        img = cv2.resize(img, (int(c / zoom), int(l / zoom)))

                    # Convert color order if necessary
                    if color and self.camera_list[cam_no].color_order == "RGB":
                        img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

                    # Show image and run cv2 event loop
                    cv2.imshow(f"cam{cam_no:}", img)
            k = cv2.waitKey(1)
            if k != -1:
                self.ask_exit()
            await asyncio.sleep(0.1)
        cv2.destroyAllWindows()
