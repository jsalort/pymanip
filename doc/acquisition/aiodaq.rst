Asynchronous acquisition
========================

The :mod:`pymanip.aiodaq` implements acquisition cards in a similar manner as :mod:`pymanip.video`
for cameras. The acquisition system (currently DAQmx or Scope) are represented with a single
object-oriented interface, to allow to easily switch between different cards, and possibly acquire on
several systems concurrently.

In addition, it provides a full GUI with both oscilloscope and signal analyser tools. This oscilloscope
GUI can be invoked directly from the command line (see :ref:`oscillo`):

.. code-block:: bash

    $ python -m pymanip oscillo

Like the other sub-modules in :mod:`pymanip`, it is built with python standard :mod:`asyncio` module,
so it can be easily mixed up with :mod:`pymanip.asyncsession`, :mod:`pymanip.aioinstruments` and
:mod:`pymanip.video`.

Usage
-----

To use the module, simply instantiate one of the concrete class, :class:`~pymanip.aiodaq.daqmx.DAQSystem`
or :class:`~pymanip.aiodaq.scope.ScopeSystem`, and use their context manager. Then, the configuration
is done with the methods such as :meth:`~pymanip.aiodaq.AcquisitionCard.add_channel` and 
:meth:`~pymanip.aiodaq.AcquisitionCard.configure_clock`, and reading is initiated and performed with the
:meth:`~pymanip.aiodaq.AcquisitionCard.start`, :meth:`~pymanip.aiodaq.AcquisitionCard.read` and
:meth:`~pymanip.aiodaq.AcquisitionCard.stop` methods.

Example with a Scope device:

.. code-block:: python

    import asyncio
    from pymanip.aiodaq import TerminalConfig
    from pymanip.aiodaq.scope import ScopeSystem, possible_sample_rates

    async def main():
        with ScopeSystem('Dev3') as scope:
            scope.add_channel('0', TerminalConfig.RSE,
                              voltage_range=10.0)
            scope.configure_clock(sample_rate=min(possible_sample_rates),
                                  samples_per_chan=1024)
            scope.start()
            d = await scope.read(tmo=1.0)
            await scope.stop()
        return d

    asyncio.run(main())
