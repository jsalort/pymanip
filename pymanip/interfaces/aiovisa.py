"""Asynchronous extension of :class:`fluidlab.interfaces.VISAInterface` (:mod:`pymanip.interfaces.aiovisa`)
===========================================================================================================

This module defines :class:`AsyncVISAInterface` as a subclass of :class:`fluidlab.interfaces.visa_inter.VISAInterface` and
:class:`pymanip.interface.aiointer.AsyncQueryInterface`.

.. autoclass:: AsyncVISAInterface
   :members:
   :private-members:

"""

import asyncio
import fluidlab.interfaces.visa_inter as fl_visa
from pymanip.interfaces.aiointer import AsyncQueryInterface

VISALock = asyncio.Lock()


class AsyncVISAInterface(fl_visa.VISAInterface, AsyncQueryInterface):
    """This class is an asynchronous extension of :class:`fluidlab.interfaces.visa_inter.VISAInterface`.
    The parameters are the same as those of the :class:`fluidlab.interfaces.visa_inter.VISAInterface` class.

    """

    def __init__(self, resource_name, backend=None):
        """Constructor method
        """
        super().__init__(resource_name, backend)
        # Override interface lock with global VISA lock because VISA library is not
        # thread-safe so we don't want concurrent calls to VISA lib.
        self.lock = VISALock

    async def await_for_srq(self, timeout=None):
        """This co-routine method acquires the interface lock and run wait_for_srq in an
        executor.
        """
        async with self.lock:
            await self.loop.run_in_executor(None, self.wait_for_srq, timeout)
