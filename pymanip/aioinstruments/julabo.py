"""

Asynchroneous extension of Julabo

"""

import fluidlab.instruments.chiller.julabo as fl_ju
from pymanip.aioinstruments.aiodrivers import AsyncDriver
from pymanip.aioinstruments.aiofeatures import (
    AsyncFloatValue,
    AsyncBoolValue,
    AsyncValue,
    AsyncIntValue,
)


class AsyncJulabo(AsyncDriver, fl_ju.Julabo):
    async def __aenter__(self):
        await super().__aenter__()
        identification = await self.interface.aquery("version")
        print("identification =", repr(identification))
        return self


afeatures = [
    AsyncFloatValue(
        "setpoint",
        channel_argument=True,
        check_instrument_value=False,
        pause_instrument=0.5,
        command_get="in_sp_{channel:02d}",
        command_set="out_sp_{channel:02d} {value:.1f}",
    ),
    AsyncBoolValue(
        "onoff",
        command_set="out_mode_05",
        pause_instrument=0.5,
        check_instrument_value=False,
    ),
    AsyncFloatValue("temperature", pause_instrument=0.75, command_get="in_pv_00"),
    AsyncIntValue(
        "setpoint_channel",
        check_instrument_value=False,
        pause_instrument=0.5,
        command_get="in_mode_01",
        command_set="out_mode_01",
    ),
    AsyncValue("status", pause_instrument=0.5, command_get="status"),
]

AsyncJulabo._build_class_with_features(afeatures)
