"""

Async Stanford Resarch SR830 extension

"""

import fluidlab.instruments.amplifier.stanford_sr830 as fl_sr830
from pymanip.aioinstruments.aiofeatures import AsyncFloatValue
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488


class AsyncStanfordSR830SenseValue(AsyncFloatValue, fl_sr830.StanfordSR830SenseValue):
    async def aget(self):
        value = await super().aget()
        return self.sense_values[int(value)]

    async def set(self, value):
        await super().aset(self.sense_values.index(value))


class AsyncStanfordSR830TCValue(AsyncFloatValue, fl_sr830.StanfordSR830TCValue):
    async def aget(self):
        value = await super().aget()
        return self.tc_values[int(value)]

    async def aset(self, value):
        await super().aset(self.tc_values.index(value))


class AsyncStanfordSR830OffsetValue(AsyncFloatValue, fl_sr830.StanfordSR830OffsetValue):
    pass


class AsyncStanfordSR830ExpandValue(AsyncFloatValue, fl_sr830.StanfordSR830ExpandValue):
    pass


class AsyncStanfordSR830(AsyncIEC60488, fl_sr830.StanfordSR830):
    pass


afeatures = [
    AsyncFloatValue(
        "angle", doc="""Angle of the demodulated signal""", command_get="OUTP ? 4"
    ),
    AsyncFloatValue(
        "freq",
        doc="""Frequency of the excitation""",
        command_get="FREQ ?",
        command_set="FREQ",
    ),
    AsyncFloatValue(
        "mag", doc="""Magnitude of the demodulated signal""", command_get="OUTP ? 3"
    ),
    AsyncStanfordSR830OffsetValue(
        "offset",
        doc="""Channel offset in % of Sen (channel value is 1 or 2)""",
        command_get="OEXP ? {channel}",
        command_set="OEXP {channel},{value},0",
        channel_argument=True,
    ),
    AsyncStanfordSR830ExpandValue(
        "expand",
        doc="""Channel expand coefficient (channel value is 1 or 2)""",
        command_get="OEXP ? {channel}",
        command_set="OEXP {channel},{value},0",
        channel_argument=True,
    ),
    AsyncFloatValue(
        "reference_phase",
        doc="""Phase shift in degrees""",
        command_get="PHAS ?",
        command_set="PHAS",
    ),
    AsyncFloatValue(
        "vrms",
        doc="""RMS Voltage of the excitation""",
        command_get="SLVL ?",
        command_set="SLVL",
    ),
    AsyncFloatValue(
        "x", doc="""Demodulated value at theta=0""", command_get="OUTP ? 1"
    ),
    AsyncFloatValue(
        "y", doc="""Demodulated value at theta=90°""", command_get="OUTP ? 2"
    ),
    AsyncStanfordSR830SenseValue(),
    AsyncStanfordSR830TCValue(),
]

AsyncStanfordSR830._build_class_with_features(afeatures)
