"""

Asynchronous extension of fluidlab SerialInterface

"""

import fluidlab.interfaces.serial_inter as fl_serial
from pymanip.interfaces.aiointer import AsyncQueryInterface


class AsyncSerialInterface(fl_serial.SerialInterface, AsyncQueryInterface):
    pass
