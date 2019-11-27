Asynchronous Session
====================

Introduction
------------

The :class:`pymanip.asyncsession.AsyncSession` class provides tools to manage an 
asynchronous experimental session. It is the main tool that we use to set up monitoring 
of experimental systems, alongside FluidLab_ device management facilities.
It will manage the storage for the data, as well as 
several asynchronous functions for use during the monitoring of the experimental system such as 
live plot of monitored data, regular control email, and remote HTTP access to the live data by 
human (connection from a web browser [#f1]_), or by a machine using the
:class:`pymanip.asyncsession.RemoteObserver` class.
It has methods to access the data for processing during the experiment, or post-processing
after the experiment is finished.

For synchronous session, one can still use the deprecated classes from :mod:`pymanip.session`,
but these will no longer be updated, therefore the asynchronous session should now always be
preferred.

Data management
---------------

AsyncSession objects can store three kinds of data:

- scalar variables monitored in time at possibly irregular time intervals. Scalar values of these variables are logged, in a “data logger” manner. They are suited to the monitoring of quantities over time when a regular measurement rate is not required. We call them “logged variables”. Tasks can save values by calling the :meth:`pymanip.asyncsession.AsyncSession.add_entry` method, and they can be later retrieved by calling the following methods :meth:`pymanip.asyncsession.AsyncSession.logged_variables`, :meth:`pymanip.asyncsession.AsyncSession.logged_variable`, :meth:`pymanip.asyncsession.AsyncSession.logged_data`, :meth:`pymanip.asyncsession.AsyncSession.logged_first_values`, :meth:`pymanip.asyncsession.AsyncSession.logged_last_values`, :meth:`pymanip.asyncsession.AsyncSession.logged_data_fromtimestamp`, or by using the `sesn[varname]` syntax shortcut which is equivalent to the :meth:`logged_variable` method.

- scalar parameter defined once in the session. We call them “parameters”. A program can save parameters with the :meth:`pymanip.asyncsession.AsyncSession.save_parameter` method, and they can be later retrieved by calling the :meth:`pymanip.asyncsession.AsyncSession.parameter`, :meth:`pymanip.asyncsession.AsyncSession.parameters`, :meth:`pymanip.asyncsession.AsyncSession.has_parameter` methods.

- non-scalar variables monitored in time at possibly irregular time intervals. A non-scalar value is typically a numpy array from an acquisition card or a frame from a camera. We call them “datasets”. They can be saved with the :meth:`pymanip.asyncsession.AsyncSession.add_dataset` method, and later be retrieved by the :meth:`pymanip.asyncsession.AsyncSession.dataset`, :meth:`pymanip.asyncsession.AsyncSession.datasets`,  :meth:`pymanip.asyncsession.AsyncSession.dataset_names`, :meth:`pymanip.asyncsession.AsyncSession.dataset_last_data`, :meth:`pymanip.asyncsession.AsyncSession.dataset_times` methods.

Task management
---------------

The main entry point for an experimental session is the :meth:`pymanip.asyncsession.AsyncSession.monitor` function which should be awaited from the main function of the program. The typical main structure of a program is then:

.. code-block:: python

    async def monitoring_task(sesn):
        some_value = await sesn.some_device.aget()
        sesn.add_entry(some_value=some_value)
        await sesn.sleep(10)

    async def main(sesn):
        async with SomeDevice() as sesn.some_device:
            await sesn.monitor(monitoring_task)

    with AsyncSession() as sesn:
        asyncio.run(main(sesn))

In this example, we see the use of the context managers, both for the :class:`AsyncSession` object,
and for the instrument object. The main experimental measurement lies in the :func:`monitoring_task` function, which should not be an explicit `for` loop. Indeed, the :meth:`sesn.monitor` method will implement the `for` loop, with checks for the interruption signal.

Possible additionnal initialisation of devices can be added to the :func:`main` function. Possible additionnal initalisation of session variables can be added in the `with AsyncSession()` block.
Note that all functions take the session object as its first argument. It is therefore possible to write the same code as a subclass of :class:`AsyncSession`, but this is not strictly necessary.

The benefits of the asynchronous structure of the example program is clearer when plotting tasks,
and email tasks are added, or when there are several concurrent monitoring tasks. The :func:`main`
function may then become:

.. code-block:: python

    async def main(sesn):
        async with SomeDevice() as sesn.some_device:
            await sesn.monitor(monitoring_task_a,
                               monitoring_task_b,
                               sesn.plot(['var_a', 'var_b', 'var_c']),
                               sesn.send_email(from_addr='toto@titi.org',
                                               to_addrs='tata@titi.org',
                                               delay_hours=2.0),
                               )

The useful pre-defined tasks are :meth:`pymanip.asyncsession.AsyncSession.send_email`, :meth:`pymanip.asyncsession.AsyncSession.plot` and :meth:`pymanip.asyncsession.AsyncSession.sweep`.

Remote access
-------------

The :meth:`pymanip.asyncsession.AsyncSession.monitor` method will set up a HTTP server for remote
access to the live data. The server can be reached from a web browser, or from another script
with an instance of the :class:`pymanip.asyncsession.RemoteObserver` class.

The usage of the `RemoteObserver` class is straightforward:

.. code-block:: python

    observer = RemoteObserver('remote-computer.titi.org')
    observer.start_recording()
    # ... some time consuming task ...
    data = observer.stop_recording()

`data` is a dictionnary which contains all the scalar variables saved on `remote-computer.titi.org`
during the time consuming task.

.. automodule:: pymanip.asyncsession

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. [#f1] The default port is 6913, but it can be changed, or turned off by passing appropriate argument to :meth:`pymanip.asyncsession.AsyncSession.monitor`.
