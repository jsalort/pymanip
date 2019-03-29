"""

Concrete implementation with niscope
(tested only for PXI-5922)

"""

import asyncio
import time
import warnings

from niScope import Scope

from pymanip.aiodaq import TriggerConfig, AcquisitionCard

possible_sample_rates = [60e6/n for n in range(4, 1201)]


class ScopeSystem(AcquisitionCard):

    def __init__(self, scope_name=None):
        super(ScopeSystem, self).__init__()
        self.scope_name = scope_name
        if scope_name:
            self.scope = Scope(scope_name)

    @property
    def samp_clk_max_rate(self):
        return max(possible_sample_rates)

    def close(self):
        if self.scope:
            self.scope.close()
            self.scope = None

    def add_channel(self, channel_name, terminal_config, voltage_range):
        cn = str(channel_name)
        if '/' in cn:
            scope_name, cn = cn.split('/')
        else:
            scope_name = self.scope_name
        if not self.scope:
            self.scope_name = scope_name
            self.scope = Scope(scope_name)
        if cn not in self.channels:
            self.channels.append(cn)
            self.scope.ConfigureVertical(channelList=channel_name,
                                         voltageRange=voltage_range)
            actual_range = self.scope.ActualVoltageRange(channel_name)
            if actual_range != voltage_range:
                warnings.warn(f'Actual range is {actual_range:} '
                              f'for chan {channel_name:}.',
                              ValueError)

    def configure_clock(self, sample_rate, samples_per_chan):
        self.scope.ConfigureHorizontalTiming(sampleRate=sample_rate,
                                             numPts=samples_per_chan)
        self.scope.NumRecords = 1
        self.sample_rate = self.scope.ActualSamplingRate
        self.samples_per_chan = self.scope.ActualRecordLength

    def configure_trigger(self, trigger_source=None, trigger_level=0,
                          trigger_config=TriggerConfig.EdgeRising):
        if trigger_source is None:
            self.scope.ConfigureTrigger('Immediate')
        else:
            trigger_source = str(trigger_source)
            if '/' in trigger_source:
                scope_name, trigger_source = trigger_source.split('/')
                if scope_name != self.scope_name:
                    raise ValueError('Wrong trigger source')

    def start(self):
        self.scope.ConfigureTrigger('Immediate')
        self.scope.InitiateAcquisition()
        self.running = True

    async def stop(self):
        self.running = False
        while self.reading:
            await asyncio.sleep(1.0)

    async def read(self):
        self.reading = True
        tmo = int(self.samples_per_chan*self.sample_rate)*2
        data = await self.loop.run_in_executor(None,
                                               self.scope.Fetch,
                                               ",".join(self.channels),
                                               None,
                                               tmo)
        self.last_read = time.monotonic()
        self.reading = False
        return data
