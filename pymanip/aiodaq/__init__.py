"""

asyncio-based abstract DAQ classes.

Concrete implementations with NI-DAQmx and NI-Scope.

"""

import asyncio
from enum import IntEnum


class TerminalConfig(IntEnum):
    RSE = 0
    NRSE = 1
    Diff = 2
    PseudoDiff = 3


class TriggerConfig(IntEnum):
    EdgeRising = 0


class AcquisitionCard:

    def __init__(self):
        self.channels = []
        self.running = False
        self.last_read = 0
        self.sample_rate = None
        self.samples_per_chan = 1
        self.loop = asyncio.get_event_loop()

    @property
    def samp_clk_max_rate(self):
        return 0

    def close(self):
        raise NotImplementedError()

    def add_channel(self, channel_name, terminal_config, voltage_range):
        raise NotImplementedError()

    def configure_clock(self, sample_rate, samples_per_chan):
        raise NotImplementedError()

    def configure_trigger(self, trigger_source=None, trigger_level=0,
                          trigger_config=TriggerConfig.EdgeRising):
        """
        If trigger_source is None, switch to Immediate trigger
        """
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    async def stop(self):
        raise NotImplementedError()

    async def read(self):
        raise NotImplementedError()
