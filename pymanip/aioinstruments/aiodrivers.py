"""Asynchronous Instrument drivers (:mod:`pymanip.aioinstruments.aiodrivers`)
=============================================================================

This module defines a subclass of :class:`fluidlab.instruments.drivers.Driver` where
the QueryInterface attribute is replaced by the corresponding AsyncQueryInterface
instance. The asynchronous context manager is bound to the interface asynchronous context
manager.

.. autofunction:: interface_from_string

.. autoclass:: AsyncDriver
   :members:
   :private-members:


"""

import fluidlab.interfaces as flinter
import fluidlab.instruments.features as flfeatures
import fluidlab.instruments.drivers as fldrivers

from pymanip.interfaces.aiointer import AsyncQueryInterface


def interface_from_string(name, default_physical_interface=None, **kwargs):
    """This function is similar to :func:`fluidlab.interfaces.interface_from_string` except
    that it returns an instance of :class:`AsyncQueryInterface` instead of :class:`QueryInterface`.
    """

    classname, physical_interface = flinter.interface_classname_from_string(
        name, default_physical_interface, **kwargs
    )

    if classname == "VISAInterface":
        from pymanip.interfaces.aiovisa import AsyncVISAInterface

        return AsyncVISAInterface(name, **kwargs)
    elif classname == "SerialInterface":
        from pymanip.interfaces.aioserial import AsyncSerialInterface

        return AsyncSerialInterface(name, **kwargs)
    elif classname == "GPIBInterface":
        from pymanip.interfaces.aiogpib import AsyncGPIBInterface

        if name.startswith("GPIB"):
            board_name, instrument_adress, *others = name.split("::")

            board_adress = int(board_name[4:])
            instrument_adress = int(instrument_adress)

        return AsyncGPIBInterface(board_adress, instrument_adress)

    raise NotImplementedError()


class AsyncDriver(fldrivers.Driver):
    """This class is an asynchronous extension of :class:`fluidlab.instruments.drivers.Driver`.
    """

    def __init__(self, interface=None):
        """Constructor method
        """
        if isinstance(interface, str):
            interface = interface_from_string(
                interface, self.default_physical_interface, **self.default_inter_params
            )
        elif not isinstance(interface, AsyncQueryInterface):
            raise ValueError("Interface should be an AsyncQueryInterface")

        super().__init__(interface)

    async def __aenter__(self):
        """Asynchronous context manager enter method
        """
        await self.interface.__aenter__()
        return self

    async def __aexit__(self, type_, value, cb):
        """Asynchronous context manager exit method
        """
        await self.interface.__aexit__(type_, value, cb)
