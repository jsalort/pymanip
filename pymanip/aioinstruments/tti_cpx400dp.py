"""Asynchronous TTI CPX400dp extension (:mod:`pymanip.aioinstruments.tti_cpx400dp`)
===================================================================================

.. autoclass:: AsyncTtiCp400dp
   :members:
   :private-members:

"""

import fluidlab.instruments.powersupply.tti_cpx400dp as fl_tti
from pymanip.aioinstruments.aiofeatures import AsyncFloatValue, AsyncBoolValue
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488


class AsyncTtiCpx400dpUnitValue(AsyncFloatValue, fl_tti.TtiCpx400dpUnitValue):
    pass


class AsyncTtiCpx400dp(AsyncIEC60488, fl_tti.TtiCpx400dp):
    pass


afeatures = [
    AsyncTtiCpx400dpUnitValue(
        "vdc",
        doc="Get actual voltage/Set voltage setpoint on specified channel",
        command_set="V{channel:d} {value}",
        command_get="V{channel:d}O?",
        channel_argument=True,
        check_instrument_value=False,
    ),
    AsyncTtiCpx400dpUnitValue(
        "idc",
        doc="Get actual current/Set current setpoint on specified channel",
        command_set="I{channel:d} {value}",
        command_get="I{channel:d}O?",
        channel_argument=True,
        check_instrument_value=False,
    ),
    AsyncBoolValue(
        "onoff",
        doc="Toogle output ON/OFF for specified channel",
        command_set="OP{channel:d} {value}",
        command_get="OP{channel:d}?",
        channel_argument=True,
        check_instrument_value=False,
        true_string="1",
        false_string="0",
    ),
    AsyncBoolValue(
        "onoffall",
        doc="Toogle output ON/OFF for both channels simultaneously",
        command_set="OPALL ",
        channel_argument=False,
        check_instrument_value=False,
        true_string="1",
        false_string="0",
    ),
]

AsyncTtiCpx400dp._build_class_with_features(afeatures)
