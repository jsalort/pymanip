"""

Concrete implementation with niscope
(tested only for PXI-5922)

"""

import asyncio
import time
import warnings
import subprocess as sp

from niScope import Scope, SLOPE, TRIGGER_SOURCE, ScopeException

from pymanip.aiodaq import TriggerConfig, AcquisitionCard, TimeoutException

try:
    from pymanip.aiodaq.daqmx import get_device_list as daqmx_get_devices

    has_daqmx = True
except ImportError:
    has_daqmx = False
try:
    from pymanip.nisyscfg import scope_devices

    has_nisyscfg = True
except (ImportError, OSError):
    has_nisyscfg = False

possible_sample_rates = [60e6 / n for n in range(4, 1201)]


class ScopeSystem(AcquisitionCard):
    def __init__(self, scope_name=None):
        super(ScopeSystem, self).__init__()
        self.scope_name = scope_name
        if scope_name:
            self.scope = Scope(scope_name)
        else:
            self.scope = None
        self.trigger_set = False

    @property
    def samp_clk_max_rate(self):
        return max(possible_sample_rates)

    def possible_trigger_channels(self):
        return ["Ext"] + self.channels

    def close(self):
        if self.scope:
            self.scope.close()
            self.scope = None

    def add_channel(self, channel_name, terminal_config, voltage_range):
        cn = str(channel_name)
        if "/" in cn:
            scope_name, cn = cn.split("/")
        else:
            scope_name = self.scope_name
        if not self.scope:
            self.scope_name = scope_name
            self.scope = Scope(scope_name)
        if cn not in self.channels:
            self.channels.append(cn)
            self.scope.ConfigureVertical(channelList=cn, voltageRange=voltage_range)
            actual_range = self.scope.ActualVoltageRange(cn)
            self.actual_ranges.append(actual_range)
            if actual_range != voltage_range:
                warnings.warn(
                    f"Actual range is {actual_range:} " f"for chan {cn:}.",
                    RuntimeWarning,
                )

    def configure_clock(self, sample_rate, samples_per_chan):
        if sample_rate not in possible_sample_rates:
            initial_sample_rate = sample_rate
            chosen = possible_sample_rates[0]
            for pos in possible_sample_rates:
                if abs(sample_rate - pos) < abs(chosen - pos):
                    chosen = pos
            sample_rate = chosen
            warnings.warn(
                f"{initial_sample_rate:} is not possible. "
                f"Closest sample rate is {sample_rate:}",
                RuntimeWarning,
            )
        self.scope.ConfigureHorizontalTiming(
            sampleRate=sample_rate, numPts=samples_per_chan
        )
        self.scope.NumRecords = 1
        self.sample_rate = self.scope.ActualSamplingRate
        self.samples_per_chan = self.scope.ActualRecordLength
        print("sample_rate =", self.sample_rate)

    def configure_trigger(
        self,
        trigger_source=None,
        trigger_level=0,
        trigger_config=TriggerConfig.EdgeRising,
    ):
        if trigger_source is None:
            print("Setting trigger to Immediate")
            self.scope.ConfigureTrigger("Immediate")
        else:
            trigger_source = str(trigger_source)
            if "/" in trigger_source:
                scope_name, trigger_source = trigger_source.split("/")
                if scope_name != self.scope_name:
                    raise ValueError("Wrong trigger source")
            print(
                "Setting trigger_source to", trigger_source, "level to", trigger_level
            )
            if trigger_source == "Ext":
                trigger_source = TRIGGER_SOURCE.EXTERNAL
            try:
                trigger_source = trigger_source.encode("ascii")
            except AttributeError:
                pass
            self.scope.ConfigureTrigger(
                "Edge",
                triggerSource=trigger_source,
                slope=SLOPE.POSITIVE,
                level=float(trigger_level),
            )
        self.trigger_set = True

    def start(self):
        if not self.trigger_set:
            self.configure_trigger()
        self.scope.InitiateAcquisition()
        self.running = True

    async def stop(self):
        if self.running:
            self.running = False
            while self.reading:
                await asyncio.sleep(1.0)
            self.scope.Abort()

    async def read(self, tmo=None):
        self.reading = True
        start = time.monotonic()
        data = None
        while self.running:
            try:
                data = await self.loop.run_in_executor(
                    None, self.scope.Fetch, ",".join(self.channels), None, 1.0
                )
                break
            except ScopeException:
                if tmo and time.monotonic() - start > tmo:
                    raise TimeoutException()
                else:
                    continue
        if data is not None:
            self.last_read = time.monotonic()
            if len(self.channels) > 1:
                data = data.T
            else:
                data = data[:, 0]
        self.reading = False
        return data


def get_device_list(daqmx_devices=None, verbose=False):
    if has_nisyscfg:
        return {
            f"{devname:} (scope)": [f"{devname:}/{ii:d}" for ii in range(2)]
            for devname in scope_devices()
        }
    else:
        # NI-Scope backend
        # In principle, use nisyscfg, see essai_nisyscfg.py (does not work
        # on old Linux where NI System Configuration is too old.)
        # Workaround: call nilsdev. Any device not previously found by the
        # DAQmx backend is a NI-Scope (presumably)
        # (Only works on Linux, because there is no nilsdev on Windows)

        raw_data = sp.run("/usr/local/bin/nilsdev", capture_output=True)
        boards = dict()
        for line in raw_data.stdout.decode("ascii").split("\n"):
            line = line.strip()
            if "[Not Present]" in line:
                continue
            if not line:
                continue
            board_type, desc = line.split(":")
            desc = desc.strip()
            board_type = board_type.strip()
            if desc.startswith('"') and desc.endswith('"'):
                devname = desc[1:-1]
                boards[devname] = board_type
            else:
                print("Wrong format", desc)
        if daqmx_devices is None:
            if has_daqmx:
                daqmx_devices = daqmx_get_devices()
            else:
                print("Could not make sure boards are NI-Scope and not DAQmx")
                daqmx_devices = dict()
        for daqmx_board_desc, daqmx_devlist in daqmx_devices.items():
            board, devnum = daqmx_devlist[0].split("/")
            if verbose:
                print("DAQmx board:", board)
            if board in boards:
                del boards[board]
                if verbose:
                    print(f"Removing board {board:} from NI-Scope list.")
        return {
            f"{devname:} ({board_type:})": [f"{devname:}/{ii:d}" for ii in range(2)]
            for devname, board_type in boards.items()
        }
