Simple usage
============

Context manager
---------------

First of all, the :class:`~pymanip.video.Camera` object uses context manager
to ensure proper opening and closing of the camera connection. This is
true for all the methods, synchronous or asynchronous.
Therefore, all our example will have a block like this:

.. code-block:: python

    from pymanip.video.avt import AVT_Camera as Camera

    with Camera() as cam:

        # ... do something with the camera ...

And in all cases, switching to another camera, for example to a PCO camera,
only requires to change the import statement, e.g.

.. code-block:: python

    from pymanip.video.pco import PCO_Camera as Camera

    with Camera() as cam:

        # ... do something with the camera ...

Simple high-level acquisition function
--------------------------------------

The easiest way to do an image acquisition with :mod:`pymanip` is to use the
high-level :meth:`~pymanip.video.Camera.acquire_to_files` method. It is a
one-liner that will start the camera, acquire the desired number of frames,
and save them on the disk. It is enough for very simple acquisition programs.
Parameters of the acquisition can be set with dedicated methods beforehands,
such as,

- :meth:`~pymanip.video.Camera.set_exposure_time`

- :meth:`~pymanip.video.Camera.set_trigger_mode`

- :meth:`~pymanip.video.Camera.set_roi`

- :meth:`~pymanip.video.Camera.set_frame_rate`


The advantage over direct calls to modules like :mod:`pymba` or :mod:`AndorNeo`
is that it is straightforward to switch camera, without changing the user-level
acquisition code.

A simple acquisition script, for use with an external GBF clock, would be:

.. code-block:: python

    import numpy as np
    from pymanip.video.avt import AVT_Camera as Camera

    acquisition_name = "essai_1"
    nframes = 3000

    with Camera() as cam:
        cam.set_trigger_mode(True) # set external trigger
        count, dt = cam.acquire_to_files(
            nframes, 
            f"{acquisition_name:}/img",
            dryrun=False,
            file_format="png",
            compression_level=9,
            delay_save=True,
        )

    dt_avg = np.mean(t[1:] - t[:-1])
    print("Average:", 1.0 / dt_avg, "fps")

The returned image is an instance of :class:`~pymanip.video.MetadataArray`, which is an extension of
:class:`numpy.ndarray` with an additionnal :attr:`~pymanip.video.MetadataArray.metadata` attribute.
When possible, the :class:`~pymanip.video.Camera` concrete subclasses set this metadata
attribute with two key-value pairs:

- "timestamp";
- "counter".

The "timestamp" key is the frame timestamp in camera clock time. The "counter" key is the frame number.

Generator method
----------------

It is sometimes desirable to have more control over what to do with the
frames. In this case, we can use the :meth:`~pymanip.video.Camera.acquisition`
generator method. The parameters are similar to the 
:meth:`~pymanip.video.Camera.acquire_to_files` method, except that the frame
will be yielded by the generator, and the user is responsible to do the
processing and saving.

The previous example can be rewritten like this:

.. code-block:: python

    import numpy as np
    import cv2
    from pymanip.video.avt import AVT_Camera as Camera

    acquisition_name = "essai_1"
    nframes = 3000
    compression_level = 9
    params = (cv2.IMWRITE_PNG_COMPRESSION, compression_level)
    t = np.zeros((nframes,))

    with Camera() as cam:

        for i, frame in enumerate(cam.acquisition(nframes)):
            filename = f"{acquisition_name:}/img-{i:04d}.png"
            cv2.imwrite(filename, frame, params)
            t[i] = frame.metadata["timestamp"].timestamp()

    dt_avg = np.mean(t[1:] - t[:-1])
    print("Average:", 1.0 / dt_avg, "fps")

Of course, the advantage of the generator method is more apparent when you
want to do more than what the :meth:`~pymanip.video.Camera.acquire_to_files`
does.
