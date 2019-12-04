"""Asynchronous TDK Lambda extension (:mod:`pymanip.aioinstruments.tdk_lambda`)
===============================================================================

.. autoclass:: AsyncTdkLambda
   :members:
   :private-members:

"""

import fluidlab.instruments.powersupply.tdk_lambda as fl_tdk
from pymanip.aioinstruments.aiofeatures import AsyncFloatValue, AsyncBoolValue
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488


class AsyncTdkLambda(AsyncIEC60488, fl_tdk.TdkLambda):
    pass


afeatures = [
    AsyncFloatValue(
        "idc",
        doc="Get actual current/Set current setpoint",
        command_get="MEAS:CURR?",
        command_set=":CURRENT",
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
        command_set="OUTPUT:STATE",
        check_instrument_value=False,
        pause_instrument=0.1,
    ),
]

AsyncTdkLambda._build_class_with_features(afeatures)
