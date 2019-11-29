Remote access
=============

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
