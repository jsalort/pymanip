Asynchronous Session
====================

.. _AsyncSession:

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

Read-only access to the asyncsession data can be achieved with the :class:`pymanip.asyncsession.SavedAsyncSession`
class.

For synchronous session, one can still use the deprecated classes from :mod:`pymanip.session`,
but these will no longer be updated, therefore the asynchronous session should now always be
preferred.

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   asyncdata
   asynctask
   asyncremote
   asyncimplementation

.. _FluidLab: https://fluidlab.readthedocs.io/en/latest/

.. [#f1] The default port is 6913, but it can be changed, or turned off by passing appropriate argument to :meth:`pymanip.asyncsession.AsyncSession.monitor`.
