"""

Async Instrument features and drivers

"""

import fluidlab.interfaces as flinter
import fluidlab.instruments.features as flfeatures
import fluidlab.instruments.drivers as fldrivers
from pymanip.interfaces.aiointer import AsyncQueryInterface


def interface_from_string(name, default_physical_interface=None, **kwargs):

    inter = flinter.interface_from_string(default_physical_interface, **kwargs)
    return AsyncQueryInterface(inter)


class AsyncDriver(fldrivers.Driver):
    def __init__(self, interface=None):

        if isinstance(interface, str):
            interface = interface_from_string(
                interface, self.default_physical_interface, **self.default_inter_params
            )
        elif not isinstance(interface, AsyncQueryInterface):
            raise ValueError("Interface should be an AsyncQueryInterface")

        super().__init__(interface)

    async def __aenter__(self):
        await self.interface.__aenter__()
        return self

    async def __aexit__(self, type_, value, cb):
        await self.interface.__exit__(type_, value, cb)
