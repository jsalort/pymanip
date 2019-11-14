"""

Asynchronous extension of fluidlab VISAInterface

"""

import fluidlab.interfaces.visa_inter as fl_visa
from pymanip.interfaces.aiointer import AsyncQueryInterface


class AsyncVISAInterface(fl_visa.VISAInterface, AsyncQueryInterface):
    pass
