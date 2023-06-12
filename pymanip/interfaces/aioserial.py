"""Asynchronous extension of :class:`~fluidlab.interfaces.serial_inter.SerialInterface` (:mod:`pymanip.interfaces.aioserial`)
=============================================================================================================================

This module defines :class:`AsyncSerialInterface` as a subclass of :class:`fluidlab.interfaces.serial_inter.SerialInterface` and
:class:`pymanip.interface.aiointer.AsyncQueryInterface`.

.. autoclass:: AsyncSerialInterface
   :members:
   :private-members:


"""
import warnings
import fluidlab.interfaces as flinter
import fluidlab.interfaces.serial_inter as fl_serial
from pymanip.interfaces.aiointer import AsyncQueryInterface


class AsyncSerialInterface(fl_serial.SerialInterface, AsyncQueryInterface):
    """This class is an asynchronous extension of :class:`fluidlab.interfaces.serial_inter.SerialInterface`.
    It inherits all its methods from the parent classes.
    """

    async def _areadlines(self, *args, **kwargs):
        """Low-level co-routine to read lines from the instrument."""
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.readlines, *args)
        return data

    async def areadlines(self, *args, **kwargs):
        """This co-routine method reads lines of data from the instrument."""
        if not self.opened:
            warnings.warn(
                "readlines() called on non-opened interface.", flinter.InterfaceWarning
            )
            self.open()
        return await self._areadlines(*args, **kwargs)
