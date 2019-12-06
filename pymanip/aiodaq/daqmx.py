"""Concrete implementation with nidaqmx-python (:mod:`pymanip.aiodaq.daqmx`)
============================================================================

This module implements a concrete implementation of the
:class:`~pymanip.aiodaq.AcquisitionCard` class using the :mod:`nidaqmx`
module.

.. autoclass:: DAQmxSystem
   :members:
   :private-members:

.. autofunction:: get_device_list

"""

import asyncio
import time

import numpy as np

from nidaqmx import Task
from nidaqmx.constants import READ_ALL_AVAILABLE
from nidaqmx.errors import DaqError
from nidaqmx.constants import TerminalConfiguration
from nidaqmx.system import system, device

from pymanip.aiodaq import (
    TerminalConfig,
    TriggerConfig,
    AcquisitionCard,
    TimeoutException,
)

ConcreteTerminalConfig = {
    TerminalConfig.RSE: TerminalConfiguration.RSE,
    TerminalConfig.NRSE: TerminalConfiguration.NRSE,
    TerminalConfig.Diff: TerminalConfiguration.DIFFERENTIAL,
    TerminalConfig.PseudoDiff: TerminalConfiguration.PSEUDODIFFERENTIAL,
}


class DAQmxSystem(AcquisitionCard):
    """This class is the concrete implementation for NI DAQmx board using
    the :mod:`nidaqmx` module.
    """

    def __init__(self):
        """Constructor method
        """
        super(DAQmxSystem, self).__init__()
        self.task = Task()
        self.reading = False
        self.stop_lock = asyncio.Lock()
        self.read_lock = asyncio.Lock()

    @property
    def samp_clk_max_rate(self):
        """Maximum sample clock rate
        """
        return self.task.timing.samp_clk_max_rate

    def possible_trigger_channels(self):
        """This method returns the list of channels that can be used as trigger.
        """
        return [chan.name for chan in self.channels]

    def close(self):
        """This method closes the active task, if there is one.
        """
        if self.task:
            self.channels = []
            self.task.close()
            self.task = None

    def add_channel(self, channel_name, terminal_config, voltage_range):
        """Concrete implementation of :meth:`pymanip.aiodaq.AcquisitionCard.add_channel`.

        .. todo::
            Actually check the type for terminal_config.

        """
        tc = ConcreteTerminalConfig[terminal_config]
        ai_chan = self.task.ai_channels.add_ai_voltage_chan(
            channel_name,
            terminal_config=tc,
            min_val=-voltage_range,
            max_val=voltage_range,
        )
        self.channels.append(ai_chan)
        self.actual_ranges.append(ai_chan.ai_max)

    def configure_clock(self, sample_rate, samples_per_chan):
        """Concrete implementation of :meth:`pymanip.aiodaq.AcquisitionCard.configure_clock`
        """
        self.task.timing.cfg_samp_clk_timing(
            sample_rate, samps_per_chan=samples_per_chan
        )
        self.sample_rate = sample_rate
        self.samples_per_chan = samples_per_chan

    def configure_trigger(
        self,
        trigger_source=None,
        trigger_level=0,
        trigger_config=TriggerConfig.EdgeRising,
    ):
        """Concrete implementation of :meth:`pymanip.aiodaq.AcquisitionCard.configure_trigger`

        .. todo::
           implement trigger_config other than the defaults value

        """

        st = self.task.triggers.start_trigger
        if trigger_source is None:
            print("disable_start_trig")
            st.disable_start_trig()
        else:
            if trigger_config != TriggerConfig.EdgeRising:
                raise NotImplementedError()  # TODO
            print(f"cfg_anlg_edge_start_trig({trigger_source:}, {trigger_level:})")
            st.cfg_anlg_edge_start_trig(trigger_source, trigger_level=trigger_level)

    def start(self):
        """This method starts the task.
        """
        self.task.start()
        self.running = True

    async def stop(self):
        """This asynchronous method aborts the current task.
        """
        async with self.stop_lock:
            if self.running:
                self.running = False
                while self.reading:
                    await asyncio.sleep(1.0)
                self.task.stop()

    async def read(self, tmo=None):
        """This asynchronous method reads data from the task.
        """
        async with self.read_lock:
            self.reading = True
            done = False
            start = time.monotonic()
            while self.running:
                try:
                    await self.loop.run_in_executor(
                        None, self.task.wait_until_done, 1.0
                    )
                except DaqError:
                    if tmo and time.monotonic() - start > tmo:
                        raise TimeoutException()
                    else:
                        continue
                done = True
                break
            if done and self.running:
                data = await self.loop.run_in_executor(
                    None, self.task.read, READ_ALL_AVAILABLE
                )
                self.last_read = time.monotonic()
                data = np.array(data)
            else:
                data = None
            self.reading = False
            return data


def get_device_list():
    """This function returns the list of devices that the NI DAQmx library
    can discover.

    :return: dictionnary with board description as key and channels as value
    :rtype: dict

    """
    sys = system.System()
    device_list = dict()
    for devname in sys.devices.device_names:
        dev = device.Device(devname)
        description = dev.product_type
        if description.startswith("PXI"):
            description = (
                f"PXI {dev.pxi_chassis_num:d} "
                f"Slot {dev.pxi_slot_num:d} "
                f"({dev.product_type:})"
            )
        elif description.startswith("PCI"):
            description = (
                f"{dev.product_type:} " f"({dev.pci_bus_num:} " f"{dev.pci_dev_num:})"
            )
        device_list[description] = dev.ai_physical_chans.channel_names
    return device_list
