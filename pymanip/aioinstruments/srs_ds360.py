"""Async Extension for Stanford Research System DS360 generator (:mod:`pymanip.aioinstruments.srs_ds360`)
=========================================================================================================

.. autoclass:: AsyncStanfordDS360
   :members:
   :private-members:

"""

import fluidlab.instruments.funcgen.srs_ds360 as fl_ds
from pymanip.aioinstruments.aiofeatures import (
    AsyncFloatScientificValue,
    AsyncFloatValue,
    AsyncBoolValue,
)
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488


class AsyncStanfordDS360(AsyncIEC60488, fl_ds.StanfordDS360):
    pass


afeatures = [
    AsyncFloatScientificValue(
        "vrms",
        doc="RMS voltage of generated wave (can be zero)",
        channel_argument=True,
        command_set="AMPL {value:.2e} VR",
        command_get="AMPL?VR",
    ),
    AsyncFloatScientificValue(
        "vdc",
        doc="Offset voltage of generated wave",
        channel_argument=True,
        command_set="OFFS {value:.2e}",
        command_get="OFFS?",
    ),
    AsyncFloatValue(
        "frequency",
        doc="Frequency of generated wave",
        command_set="FREQ",
        command_get="FREQ?",
    ),
    AsyncBoolValue(
        "onoff", doc="Output ON/OFF", command_set="OUTE", command_get="OUTE?"
    ),
    AsyncBoolValue(
        "balanced",
        doc="Output mode (balanced or unbalanced)",
        command_set="OUTM",
        command_get="OUTM?",
    ),
]

AsyncStanfordDS360._build_class_with_features(afeatures)
