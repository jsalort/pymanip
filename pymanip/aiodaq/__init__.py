"""Asynchronous Acquisition Card (:mod:`pymanip.aiodaq`)
========================================================

This module defines an abstract base class for asynchronous communication
with acquisition cards.
This is used by the live oscilloscope command line tool.

Concrete implementations are:

- :class:`pymanip.aiodaq.daqmx.DAQmxSystem` for NI DAQmx cards;

- :class:`pymanip.aiodaq.scope.ScopeSystem` for NI Scope cards.

In principle, other library bindings could be implemented.

.. autoclass:: TerminalConfig

.. autoclass:: TriggerConfig

.. autoclass:: TimeoutException

.. autoclass:: AcquisitionCard
   :members:
   :private-members:

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
    """Base class for all acquisition cards.
    The constructor takes no argument. Channels
    are added using the :meth:`~pymanip.aiodaq.daqmx.DAQmxSystem.add_channel` method,
    and the clock is configured with the
    :meth:`~pymanip.aiodaq.daqmx.DAQmxSystem.configure_clock` method.
    """

    def __init__(self):
        """Constructor method
        """
        self.channels = []
        self.actual_ranges = []
        self.running = False
        self.last_read = 0
        self.sample_rate = None
        self.samples_per_chan = 1
        self.loop = asyncio.get_event_loop()

    def __enter__(self):
        """Context manager enter method
        """
        return self

    def __exit__(self, type_, value, cb):
        """Context manager exit method
        """
        self.close()

    @property
    def samp_clk_max_rate(self):
        """Maximum sample clock rate
        """
        return 0

    def possible_trigger_channels(self):
        """This method returns the list of channels that can be used as trigger.
        """
        return self.channels

    def close(self):
        """This method closes the connection to the acquisition card.
        """
        raise NotImplementedError()

    def add_channel(self, channel_name, terminal_config, voltage_range):
        """This method adds a channel for acquisition.

        :param channel_name: the channel to add, e.g. "Dev1/ai0"
        :type channel_name: str
        :param terminal_config: the configuration of the terminal, i.e. RSE, NRSE, DIFFERENTIAL or PSEUDODIFFERENTIAL
        :type terminal_config: :class:`~pymanip.aiodaq.TerminalConfig`
        :param voltage_range: the voltage range for the channel (actual value may differ)
        :type voltage_range: float
        """
        raise NotImplementedError()

    def configure_clock(self, sample_rate, samples_per_chan):
        """This method configures the board clock for the acquisition.

        :param sample_rate: the clock frequency in Hz
        :type sample_rate: float
        :param samples_per_chan: number of samples to be read on each channel
        :type samples_per_chan: int
        """
        raise NotImplementedError()

    def configure_trigger(
        self,
        trigger_source=None,
        trigger_level=0,
        trigger_config=TriggerConfig.EdgeRising,
    ):
        """This method configures the trigger for the acquisition, i.e. internal trigger
        or triggered on one of the possible channels. The list of possible channels
        can be obtained from the
        :meth:`~pymanip.aiodaq.daqmx.DAQmxSystem.possible_trigger_channels` method.

        :param trigger_source: the channel to use for triggering, or None to disable external trigger (switch to Immeditate trigger). Defaults to None.
        :type trigger_source: str
        :param trigger_level: the voltage threshold for triggering
        :type trigger_level: float
        :param trigger_config: the kind of triggering, e.g. EdgeRising. Defaults to EdgeRising.
        :type trigger_config: :class:`pymanip.aiodaq.TriggerConfig`, optional
        """
        raise NotImplementedError()

    def start(self):
        """This method starts the acquisition
        """
        raise NotImplementedError()

    async def stop(self):
        """This asynchronous method aborts the acquisition
        """
        raise NotImplementedError()

    async def read(self, tmo=None):
        """This asynchronous method reads data from the acquisition card.
        """
        raise NotImplementedError()

    async def start_read_stop(self, tmo=None):
        """This asynchronous method starts the acquisition, reads the data, and
        stops the acquisition.

        :param tmo: timeout for reading, defaults to None
        :type tmo: float
        """
        self.start()
        data = await self.read(tmo)
        await self.stop()
        return data

    def read_sync(self, tmo=None):
        """This method is a synchronous wrapper around
        :meth:`~pymanip.aiodaq.AcquisitionCard.start_read_stop` method.
        It is a convenience facility for simple usage.
        """
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
        """This asynchronous method is a high-level method for simple case. It
        configures all the given channels, as well as the clock, then starts the
        acquisition, read the data, and stops the acquisition.

        It is essentially similar to :func:`pymanip.daq.DAQmx.read_analog`, except
        asynchronous and functionnal for other cards than DAQmx cards.

        :param resource_names: list of resources to read, e.g. ["Dev1/ai1", "Dev1/ai2"] for DAQmx cards, or name of the resource if only one channel is to be read.
        :type resource_names: list or str
        :param terminal_config: list of terminal configs for the channels
        :type terminal_config: list
        :param volt_min: minimum voltage expected on the channel
        :type volt_min: float
        :param volt_max: maximum voltage expected on the channel
        :type volt_max: float
        :param samples_per_chan: number of samples to read on each channel
        :type samples_per_chan: int
        :param sample_rate: frequency of the clock
        :type sample_rate: float
        :param coupling_type: coupling for the channel (e.g. AC or DC)
        :type coupling_type: str
        :param output_filename: filename for direct writting to the disk
        :type output_filename: str, optional
        :param verbose: verbosity level
        :type verbose: bool, optional
        """

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
        """Synchronous wrapper around :meth:`pymanip.aiodaq.AcquisitionCard.read_analog`.
        """
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(self.read_analog(*args, **kwargs))
        return data
