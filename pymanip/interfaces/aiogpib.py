"""Asynchronous extension of :class:`~fluidlab.interfaces.gpib_inter.GPIBInterface` (:mod:`pymanip.interfaces.aiogpib`)
=======================================================================================================================

This module defines :class:`AsyncGPIBInterface` as a subclass of :class:`fluidlab.interfaces.gpib_inter.GPIBInterface` and
:class:`pymanip.interface.aiointer.AsyncQueryInterface`.

.. autoclass:: AsyncGPIBInterface
   :members:
   :private-members:

"""

import asyncio
import fluidlab.interfaces.gpib_inter as fl_gpib
from pymanip.interfaces.aiointer import AsyncQueryInterface

GPIBLock = asyncio.Lock()


class AsyncGPIBInterface(fl_gpib.GPIBInterface, AsyncQueryInterface):
    """This class is an asynchronous extension of :class:`fluidlab.interfaces.gpib_inter.GPIBInterface`.
    It inherits all its methods from the parent classes.
    """

    def __init__(self, board_adress, instrument_adress):
        """Constructor method
        """
        super().__init__(board_adress, instrument_adress)
        # replace per-device lock by global GPIB lock
        self.lock = GPIBLock

    async def await_for_srq(self, timeout=None):
        """This co-routine method acquires the interface lock and run wait_for_srq in an
        executor
        """
        async with self.lock:
            await self.loop.run_in_executor(None, self.wait_for_srq, timeout)
