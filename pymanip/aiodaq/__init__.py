"""

asyncio-based abstract DAQ classes.

Concrete implementations with NI-DAQmx and NI-Scope.

"""

import asyncio
from enum import IntEnum

from pymanip.asynctools import synchronize_function


class TerminalConfig(IntEnum):
    RSE = 0
    NRSE = 1
    Diff = 2
    PseudoDiff = 3


class TriggerConfig(IntEnum):
    EdgeRising = 0


class TimeoutException(Exception):
    pass


class AcquisitionCard:
    def __init__(self):
        self.channels = []
        self.actual_ranges = []
        self.running = False
        self.last_read = 0
        self.sample_rate = None
        self.samples_per_chan = 1
        self.loop = asyncio.get_event_loop()

    def __enter__(self):
        return self

    def __exit__(self, type_, value, cb):
        self.close()

    @property
    def samp_clk_max_rate(self):
        return 0

    def possible_trigger_channels(self):
        return self.channels

    def close(self):
        raise NotImplementedError()

    def add_channel(self, channel_name, terminal_config, voltage_range):
        raise NotImplementedError()

    def configure_clock(self, sample_rate, samples_per_chan):
        raise NotImplementedError()

    def configure_trigger(
        self,
        trigger_source=None,
        trigger_level=0,
        trigger_config=TriggerConfig.EdgeRising,
    ):
        """
        If trigger_source is None, switch to Immediate trigger
        """
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    async def stop(self):
        raise NotImplementedError()

    async def read(self, tmo=None):
        raise NotImplementedError()

    async def start_read_stop(self, tmo=None):
        self.start()
        data = await self.read(tmo)
        await self.stop()
        return data

    def read_sync(self, tmo=None):
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(self.start_read_stop(tmo))
        return data

    async def read_analog(
        self,
        resource_names,
        terminal_config,
        volt_min=None,
        volt_max=None,
        samples_per_chan=1,
        sample_rate=1,
        coupling_types="DC",
        output_filename=None,
        verbose=True,
    ):

        if isinstance(resource_names, str):
            resource_names = [resource_names]
        if isinstance(terminal_config, str):
            terminal_config = [terminal_config]
        try:
            terminal_config[0]
        except TypeError:
            terminal_config = [terminal_config]
        try:
            volt_min[0]
        except TypeError:
            volt_min = [volt_min]
        try:
            volt_max[0]
        except TypeError:
            volt_max = [volt_max]

        for chan_name, chan_tc, chan_vmin, chan_vmax in zip(
            resource_names, terminal_config, volt_min, volt_max
        ):
            volt_range = max([abs(chan_vmin), abs(chan_vmax)])
            self.add_channel(chan_name, chan_tc, volt_range)
        self.configure_clock(sample_rate, int(samples_per_chan))
        self.configure_trigger(None)
        data = await self.start_read_stop()
        return data

    def read_analog_sync(self, *args, **kwargs):
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(self.read_analog(*args, **kwargs))
        return data
