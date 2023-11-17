"""Asynchronous Xantrex XDC-300 extension (:mod:`pymanip.aioinstruments.xantrex_xdc300`)
========================================================================================

.. autoclass:: AsyncXantrexXDC300
   :members:
   :private-members:

"""

import fluidlab.instruments.powersupply.xantrex_xdc300 as fl_xdc
from pymanip.aioinstruments.aiofeatures import AsyncFloatValue, AsyncBoolValue
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488


class AsyncXantrexXDC300(AsyncIEC60488, fl_xdc.XantrexXDC300):
    pass


afeatures = [
    AsyncFloatValue(
        "idc",
        doc="Get actual current/Set current setpoint",
        command_get="MEAS:CURR?",
        command_set=("SYST:REM:SOUR GPIB\n" "SYST:REM:STAT REM\n" "SOUR:CURR "),
        check_instrument_value=False,
    ),
    AsyncFloatValue(
        "vdc",
        doc="Get actual voltage/Set voltage setpoint",
        command_get="MEAS:VOLT?",
        command_set=("SYST:REM:SOUR GPIB\n" "SYST:REM:STAT REM\n" "SOUR:VOLT "),
        check_instrument_value=False,
    ),
    AsyncFloatValue(
        "wdc",
        doc="Get actual power/Set power setpoint",
        command_get="MEAS:POW?",
        command_set=("SYST:REM:SOUR GPIB\n" "SYST:REM:STAT REM\n" "SOUR:POW "),
        check_instrument_value=False,
    ),
    AsyncBoolValue(
        "onoff",
        doc="Toggle output ON/OFF",
        command_set="OUTP ",
        true_string="ON",
        false_string="OFF",
        check_instrument_value=False,
    ),
]

AsyncXantrexXDC300._build_class_with_features(afeatures)
