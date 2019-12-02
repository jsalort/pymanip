Advanced usage
==============

In this section, we illustrate a more advanced usage from one of our own
use case. We need simultaneous acquisition on two cameras. The framerate is
too fast to wait for each frame to be saved before grabbing the next one.
But we don't want to delay until the end of the acquisition (which might
still be long) to start saving, because we don't want to loose all the data
in case something bad happens, and we wish to be able to have a look at
the picture before the acquisition ends. 

So, in this example, we implement simple queues in which the frames
are stored, and there is a fourth task which gets the frames from this queue and saves them,
(at a lower rate than the acquisition rate). When the acquisition is stopped,
this last task finishes the saving.
In addition, we want to save acquisition parameters with an 
:class:`~pymanip.asyncsession.AsyncSession` object.
To summarize the four tasks:

- task0: acquisition on cam 0

- task1: acquisition on cam 1

- task2: software trigger when cams are ready

- task3: background saving of images

The first 3 tasks are similar to those in the previous section. We use
Python standard library :class:`~queue.SimpleQueue` class to implement the frame
queue.

We comment the various parts of this script in the following subsections.

Preambule
---------

First the import statements, and definition of some global parameters (video
parameter, as well as names for output files).

.. code-block:: python

    from queue import SimpleQueue
    import asyncio
    import os
    import cv2
    from datetime import datetime
    
    from pymanip.instruments import Agilent33220a
    from pymanip.video.avt import AVT_Camera
    from pymanip.asyncsession import AsyncSession
    from progressbar import ProgressBar
    
    # User inputs
    compression_level = 3
    exposure_time = 10e-3
    cam_type = "avt"
    fps = 2
    num_imgs = 10
    
    # Paths to save data
    current_date = datetime.today().strftime("%Y%m%d")
    current_dir = os.path.dirname(os.path.realpath(__file__))
    saving_dir_date = f"{current_dir}\\data\\{current_date}\\"
    if not os.path.isdir(saving_dir_date):
        os.makedirs(saving_dir_date)
    num_dir = len(os.listdir(saving_dir_date))
    saving_dir_run = f"{saving_dir_date}run{num_dir+1:02.0f}\\"
    if not os.path.isdir(saving_dir_run):
        os.makedirs(saving_dir_run)
    basename = f"{saving_dir_run}session"

Acquisition task (task 0 and task 1)
------------------------------------

This task is responsible for grabbing frames for the camera, and putting
it in the queue. Note that we must *copy* the image because the numpy
array yielded by the :meth:`~pymanip.video.Camera.acquisition_async`
generator uses shared memory (and would no longer hold this particular frame
on subsequent iterations of the generator). The queues are created in the main
function, and are called :attr:`im_buffer0` for camera 0, and :attr:`im_buffer1`
for camera 1.

In addition, we want to be able to abort the script. We use the mechanisms
defined in the :class:`pymanip.asyncsession.AsyncSession` class which set ups
signal handling for interrupt signal. It basically defines a :attr:`running`
attribute that is set to :obj:`False` when the program should stop. The
acquisition task must check this variable to cleanup stop grabbing the
frames if the user has sent the interrupt signal.

.. code-block:: python

    async def acquire_images(sesn, cam, num_cam, initialing_cams):
        global num_imgs
    
        kk = 0
        bar = ProgressBar(min_value=0, max_value=num_imgs, initial_value=kk)
        gen = cam.acquisition_async(num_imgs, initialising_cams=initialing_cams)
    
        async for im in gen:
            if num_cam == 0:
                sesn.im_buffer0.put(im.copy())
            elif num_cam == 1:
                sesn.im_buffer1.put(im.copy())
    
            kk += 1
            bar.update(kk)
            if not sesn.running:
                num_imgs = kk
                success = await gen.asend(True)
                if not success:
                    print("Unable to stop camera acquisition")
                break
        bar.finish()
    
        print(f"Camera acquisition stopped ({kk:d} images recorded).")
        sesn.running = False

Software trigger task (task 2)
------------------------------

This task monitor the set of initialising cams, which gets empty when all the cameras
are ready to grab frames. Then, it triggers the generator function.

.. code-block:: python

    async def start_clock(cams):
        # Start clocks once all camera are done initializing
        while len(cams) > 0:
            await asyncio.sleep(1e-3)
        gbf.trigger()
        return datetime.now().timestamp()

Background saving of images (task 3)
------------------------------------

This task looks for images in the :obj:`im_buffer0` and :obj:`im_buffer1` queues, as long as
the acquisition is still running or that the queues are not empty.
The images are saved using OpenCV :func:`imwrite` function that we run in an executor (i.e. in a
separate thread), so as not to block the acquisition tasks.

.. code-block:: python

    async def save_images(sesn):
        params = (cv2.IMWRITE_PNG_COMPRESSION, compression_level)
        loop = asyncio.get_event_loop()
        i = 0
        bar = None
    
        while sesn.running or not sesn.im_buffer0.empty() or not sesn.im_buffer1.empty():
            if sesn.im_buffer0.empty() and sesn.im_buffer1.empty():
                await asyncio.sleep(1.0)
            else:
                if not im_buffer0.empty():
                    im0 = sesn.im_buffer0.get()
                    filename0 = f"{saving_dir_run}\\cam0_{i:04d}.png"
                    await loop.run_in_executor(None, cv2.imwrite, filename0, im0, params)
                    i += 1
    
                if not im_buffer1.empty():
                    im1 = sesn.im_buffer1.get()
                    filename1 = f"{saving_dir_run}\\cam1_{i:04d}.png"
                    await loop.run_in_executor(None, cv2.imwrite, filename1, im1, params)

            if not sesn.running:
                if bar is None:
                    print("Saving is terminating...")
                    bar = ProgressBar(
                        min_value=0, max_value=2 * num_imgs, initial_value=2 * i
                    )
                else:
                    bar.update(2 * i)
        if bar is not None:
            bar.finish()
        print(f"{2*i:d} images saved.")

One important point is that this task is the only task which access disk storage. The acquisition tasks work
solely on memory, so they are not slowed down by the saving task.

Main function and setup
-----------------------

The main function sets up the function generator and the cameras, and start the tasks. It must also
create the queues.

.. code-block:: python

    async def main():

        with AsyncSession(basename) as sesn, \
             Agilent33220a("USB0::2391::1031::MY44052515::INSTR") as sesn.gbf:

            # Configure function generator
            sesn.gbf.configure_burst(fps, num_imgs)
            sesn.save_parameter(fps=fps, num_imgs=num_imgs)

            # Prepare buffer queues
            sesn.im_buffer0 = SimpleQueue()
            sesn.im_buffer1 = SimpleQueue()

            # Prepare camera and start tasks
            with AVT_Camera(0) as cam0, \
                 AVT_Camera(1) as cam1:

                # External trigger and camera properties
                cam0.set_trigger_mode(True)
                cam1.set_trigger_mode(True)

                cam0.set_exposure_time(exposure_time)
                cam1.set_exposure_time(exposure_time)
                sesn.save_parameter(exposure_time=exposure_time)

                cam0.camera.IIDCPacketSizeAuto = "Off"
                cam0.camera.IIDCPacketSize = 5720
                cam1.camera.IIDCPacketSizeAuto = "Off"
                cam1.camera.IIDCPacketSize = 8192 // 2

                # Set up tasks
                initialing_cams = {cam0, cam1}
                task0 = acquire_images(sesn, cam0, 0, initialing_cams)
                task1 = acquire_images(sesn, cam1, 1, initialing_cams)  
                task2 = start_clock(initialing_cams)
                task3 = save_images(sesn)

                # We use AsyncSession monitor co-routine which set ups the signal
                # handling. We don't need remote access, so server_port=None.
                # Alternative:
                # await asyncio.gather(task0, task1, task2, task3)
                await sesn.monitor(task0, task1, task2, task3,
                                   server_port=None)

    asyncio.run(main())
