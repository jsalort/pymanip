Asynchronous Extension of FluidLab Instrument Classes
=====================================================

`FluidLab Instrument classes <https://fluidlab.readthedocs.io/en/latest/generated/fluidlab.instruments.html>`_, which can be accessed from the :mod:`pymanip.instruments` module are written in a synchronous manner, i.e. all calls are blocking. However, most of the time, the program essentially waits for the instrument response.

While most scientific instruments are not designed for concurrent requests, and most library, such as National Instruments VISA, are not thread-safe, it is still desirable to have an asynchronous API for the instrument classes. This allows to keep other tasks running while waiting for (possibly long) delays. The other tasks include: communication with other types of devices on other types of boards, refreshing the GUI and responding to remote access requests.

This asynchronous extension is implemented in the :mod:`pymanip.aioinstruments` and :mod:`pymanip.interfaces.aiointer` modules. They define subclasses of FluidLab_ interface, feature are instrument classes. This is currently highly experimental, so please use it at your own risk. However, it may eventually be merged into FluidLab_ when it gets more mature.

From the user perspective, the usage of asynchronous instruments is relatively straightforward for those who already know how to use `FluidLab Instrument classes <https://fluidlab.readthedocs.io/en/latest/generated/fluidlab.instruments.html>`_.

The synchronous program

.. code-block:: python

    from pymanip.instruments import Agilent34970a
    
    def main():
        with Agilent34970a('GPIB0::9::INSTR') as a:
            R1, R2 = a.ohm_4w.get((101, 102))
        return R1, R2

becomes

.. code-block:: python

    from pymanip.aioinstruments import AsyncAgilent34970a

    async def main():
        async with AsyncAgilent34970a('GPIB0::9::INSTR') as a:
            R1, R2 = await a.ohm_4w.aget((101, 102))
        return R1, R2

The asynchronous instrument subclasses all have the "Async" prefix in their names. Asynchronous context manager *must* be used instead of the classical context manager because some specific initialisation may be done in the asynchronous interface :meth:`__aenter__` method. All the features have the same name as in the synchronous class, but they have :meth:`aget` and :meth:`aset` co-routine methods instead of :meth:`get` and :meth:`set` methods.

.. _FluidLab: https://foss.heptapod.net/fluiddyn/fluidlab
