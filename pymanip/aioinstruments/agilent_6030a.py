"""Asynchronous Agilent 6030a (:mod:`pymanip.aioinstruments.agilent_6030a`)
===========================================================================

"""

import fluidlab.instruments.powersupply.agilent_6030a as fl_ag
from pymanip.aioinstruments.aiofeatures import AsyncFloatValue, AsyncBoolValue
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488


class AsyncAgilent6030a(AsyncIEC60488, fl_ag.Agilent6030a):
    pass


afeatures = [
    AsyncFloatValue(
        "idc",
        doc="Get actual current/Set current setpoint",
        command_get="MEAS:CURR?",
        command_set="SOUR:CURR",
        check_instrument_value=False,
        pause_instrument=0.1,
    ),
    AsyncFloatValue(
        "vdc",
        doc="Get actual voltage/Set voltage setpoint",
        command_get="MEAS:VOLT?",
        command_set="SOUR:VOLT",
        check_instrument_value=False,
        pause_instrument=0.1,
    ),
    AsyncBoolValue(
        "onoff",
        doc="Toggle output ON/OFF",
        command_set="OUTP:STAT",
        check_instrument_value=False,
        pause_instrument=0.1,
    ),
]

AsyncAgilent6030a._build_class_with_features(afeatures)
