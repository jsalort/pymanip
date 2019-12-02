Asynchronous acquisition
========================

Simple asynchronous acquisition
-------------------------------

The video recording may be used as part of a larger experimental program.
In particular, you may want to keep monitoring the experiment conditions while
recording the video, and possibly save the experiment parameters next to the
video frames. The simplest way to achieve that is to implement the monitoring
task and the video recording task as asynchronous functions.

The very simple :meth:`~pymanip.video.Camera.acquire_to_files_async` method
is sufficient for very basic cases. The usage is strictly similar to
the synchronous :meth:`~pymanip.video.Camera.acquire_to_files` method described
in the previous section. In fact, the synchronous method is only a wrapper
around the asynchronous method.

The simple example of the previous section can be rewritten like this:

.. code-block:: python

    import asyncio
    import numpy as np
    from pymanip.video.avt import AVT_Camera as Camera

    async def some_monitoring():

        # ... do some monitoring of the experiment conditions ...

    async def video_recording():

        acquisition_name = "essai_1"
        nframes = 3000

        with Camera() as cam:
            cam.set_trigger_mode(True)
            count, dt = await cam.acquire_to_files_async(
                nframes, 
                f"{acquisition_name:}/img",
                dryrun=False,
                file_format="png",
                compression_level=9,
                delay_save=True,
            )

        dt_avg = np.mean(t[1:] - t[:-1])
        print("Average:", 1.0 / dt_avg, "fps")

    async def main():
        await asyncio.gather(some_monitoring(),
                             video_recording(),
                            )

    asyncio.run(main())

Multi-camera acquisition
------------------------

One application of this simple method is to extent to simultaneous acquisition
on several cameras (possibly of different brands).
To ensure simultaneous frame grabbing, it is necessary to use an external
function generator for external triggering. In the following example, we use
an Agilent 33220a function generator which we configure for a burst with
a software trigger. In our case, we use USB to communicate with the generator.
Once the two cameras are ready for frame grabbing, the software trigger is
sent, and the frames from both cameras are acquired.

Some manual tickering may be necessary in real cases. For example, in our
example we use two Firewire AVT cameras connected on the same FireWire board.
So we must adjust the packet size.

To know when both cameras are ready to grab frames, we use the 
:obj:`initialising_cams` parameter. Each camera object removes itself from
this set when it is ready to grab frames. All we need is therefore to implement
a task which will send the software trigger to the function generator, once the
set is empty.

Because the function generator is programmed for a burst of N peaks, the
cameras will only be triggered N times. Therefore, it is a way to make sure
that the N obtained frames were indeed simultaneous. If one camera skips one
frame, the total number of frame will no longer be N.

The code is as follow:

.. code-block:: python

    import asyncio
    from datetime import datetime
    from pymanip.instruments import Agilent33220a
    from pymanip.video.avt import AVT_Camera

    basename = "multi"
    fps = 10.0
    nframes = 100

    with Agilent33220a("USB0::2391::1031::MY44052515::INSTR") as gbf:

        gbf.configure_burst(fps, nframes)

        async def start_clock(cams):
            """This asynchronous function sends the software trigger to
               the gbf when all cams are ready.

               :param cams: initialising cams
               :type cams: set
               :return: timestamp of the time when the software trigger was sent
               :rtype: float
            """
            while len(cams) > 0:
                await asyncio.sleep(1e-3)
            gbf.trigger()
            return datetime.now().timestamp()

        with AVT_Camera(0) as cam0, \
             AVT_Camera(1) as cam1:

            cam0.set_trigger_mode(True)  # external trigger
            cam1.set_trigger_mode(True)
            cam0.set_exposure_time(10e-3)
            cam1.set_exposure_time(10e-3)
            cam0.camera.IIDCPacketSizeAuto = "Off"
            cam0.camera.IIDCPacketSize = 5720
            cam1.camera.IIDCPacketSizeAuto = "Off"
            cam1.camera.IIDCPacketSize = 8192 // 2

            initialing_cams = {cam0, cam1}

            task0 = cam0.acquire_to_files_async(
                nframes,
                basename + "/cam0",
                zerofill=4,
                file_format="png",
                delay_save=True,
                progressbar=True,
                initialising_cams=initialing_cams,
            )
            task1 = cam1.acquire_to_files_async(
                nframes,
                basename + "/cam1",
                zerofill=4,
                file_format="png",
                delay_save=True,
                progressbar=False,
                initialising_cams=initialing_cams,
            )
            task2 = start_clock(initialing_cams)

            tasks = asyncio.gather(task0, task1, task2)
            loop = asyncio.get_event_loop()
            (countA, dtA), (countB, dtB), t0 = loop.run_until_complete(tasks)

Note that we use the :obj:`progressbar` parameter to avoid printing two progress bars. The :meth:`acquire_to_files_async`
methods are passed the number of expected frames. If one frame is skipped, a Timeout exception will be raised.
