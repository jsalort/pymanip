"""Asynchronous LakeShore 224
=============================

.. autoclass:: AsyncLakeshore224
   :members:
   :private-members:
   :show-inheritance:

"""
import fluidlab.instruments.multiplexer.lakeshore_224 as fl_lakeshore
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488
from pymanip.aioinstruments.aiofeatures import AsyncFloatValue, AsyncIntValue


class AsyncLakeshore224(AsyncIEC60488, fl_lakeshore.Lakeshore224):
    pass


afeatures = [
    AsyncFloatValue(
        "temperature",
        doc="Reads temperature (in Kelvins)",
        command_get="KRDG? {channel:}",
        channel_argument=True,
    ),
    AsyncFloatValue(
        "sensor_value",
        doc="Reads sensor signal in sensor units",
        command_get="SRDG? {channel:}",
        channel_argument=True,
    ),
    AsyncIntValue(
        "curve_number",
        doc="Specifies the curve an input uses for temperature conversion",
        command_set="INCRV {channel:},{value:}",
        command_get="INCRV? {channel:}",
        channel_argument=True,
    ),
]

AsyncLakeshore224._build_class_with_features(afeatures)
