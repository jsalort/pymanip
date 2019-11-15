"""

Asynchronous extension of fluidlab VISAInterface

"""

import asyncio
import fluidlab.interfaces.visa_inter as fl_visa
from pymanip.interfaces.aiointer import AsyncQueryInterface

VISALock = asyncio.Lock()


class AsyncVISAInterface(fl_visa.VISAInterface, AsyncQueryInterface):
    def __init__(self, resource_name, backend=None):

        super().__init__(resource_name, backend)
        # Override interface lock with global VISA lock because VISA library is not
        # thread-safe so we don't want concurrent calls to VISA lib.
        self.lock = VISALock
