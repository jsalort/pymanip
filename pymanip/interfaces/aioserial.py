"""Asynchronous extension of :class:`~fluidlab.interfaces.serial_inter.SerialInterface` (:mod:`pymanip.interfaces.aioserial`)
=============================================================================================================================

This module defines :class:`AsyncSerialInterface` as a subclass of :class:`fluidlab.interfaces.serial_inter.SerialInterface` and
:class:`pymanip.interface.aiointer.AsyncQueryInterface`.

.. autoclass:: AsyncSerialInterface
   :members:
   :private-members:


"""

import fluidlab.interfaces.serial_inter as fl_serial
from pymanip.interfaces.aiointer import AsyncQueryInterface


class AsyncSerialInterface(fl_serial.SerialInterface, AsyncQueryInterface):
    """This class is an asynchronous extension of :class:`fluidlab.interfaces.serial_inter.SerialInterface`.
    It inherits all its methods from the parent classes.
    """

    pass
