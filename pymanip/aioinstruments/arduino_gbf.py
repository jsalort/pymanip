"""Arduino GBF Interface (:mod:`pymanip.aioinstruments.arduino_gbf`)
====================================================================

Interface for the Arduino GBF Interface (see the ino file in the Arduino
folder).

"""
import asyncio
import warnings
from time import monotonic, sleep

import numpy as np

from fluidlab.interfaces import PhysicalInterfaceType
from pymanip.aioinstruments.aiodrivers import AsyncDriver
from pymanip.aiodaq import (
    AcquisitionCard,
    TerminalConfig,
    TriggerConfig,
    TimeoutException,
)


class AsyncArduino(AsyncDriver, AcquisitionCard):
    default_physical_interface = PhysicalInterfaceType.Serial
    default_inter_params = {
        "baudrate": 9600,
        "bytesize": 8,
        "parity": "N",
        "stopbits": 1,
        "timeout": 5.0,
        "xonxoff": False,
        "rtscts": False,
        "dsrdtr": False,
        # "eol": "\r\n",
        # "autoremove_eol": True,
    }

    def __init__(self, interface, pin_output=13):
        AsyncDriver.__init__(self, interface)
        AcquisitionCard.__init__(self)
        self.pin_output = pin_output

    def __enter__(self):
        super().__enter__()
        while line := self.interface.readline().decode("ascii").strip():
            if line.startswith("GBF"):
                print("Connection established", line)
                break
            print(line)
        sleep(0.1)
        return self

    async def __aenter__(self):
        await super().__aenter__()
        start = monotonic()
        good = False
        while (monotonic() - start) < 5.0:
            identification = await self.interface.aread()
            identification = identification.decode("ascii").strip()
            if identification.startswith("GBF"):
                print("Connection to Arduino", identification)
                good = True
                break
            print(identification)
            await asyncio.sleep(0.1)
        if not good:
            raise RuntimeError("Timeout connecting to Arduino GBF")
        await asyncio.sleep(0.1)
        return self

    def close(self):
        pass

    def flush(self):
        while line := self.interface.readline().decode("ascii").strip():
            print(line)

    def add_channel(
        self, channel_name, terminal_config=TerminalConfig.RSE, voltage_range=5.0
    ):
        if hasattr(channel_name, "startswith") and channel_name.startswith("ai"):
            channel_name = channel_name[2:]
        pin_num = int(channel_name)
        self.channels = [str(pin_num)]
        if terminal_config != TerminalConfig.RSE:
            warnings.warn("Only RSE is supported")
        if voltage_range != 5.0:
            warnings.warn("Voltage range is fixed to 5.0 V")

    def configure_clock(self, sample_rate, samples_per_chan):
        self.sample_rate = sample_rate
        self.samples_per_chan = int(samples_per_chan)

    def configure_trigger(
        self,
        trigger_source=None,
        trigger_level=-5.0,
        trigger_config=TriggerConfig.EdgeRising,
    ):
        self.trigger_source = trigger_source
        self.trigger_level = trigger_level

    def start(self):
        if not hasattr(self, "trigger_level"):
            self.configure_trigger()
        delay_us = int(1e6 / self.sample_rate)
        self.interface.write(
            f"read_analog {self.channels[0]:} {self.samples_per_chan:d} {self.trigger_level:.1f} {delay_us:d}\n"
        )
        self.running = True

    async def stop(self):
        await self.interface.awrite("Abort\n")
        self.running = False

    async def read(self, tmo=None):
        self.reading = True
        start = monotonic()
        data = list()
        print("Start reading loop")
        while self.running:
            try:
                line = await self.interface.aread()
                line = line.decode("ascii").strip()
                if line.startswith("read_voltage_window FINISHED"):
                    print(line, "(breaking)")
                    break
                data.append(float(line))
            except ValueError:
                if not line:
                    print("no data (breaking)")
                    break
                print(line, "(continuing)")
                continue
            if tmo and monotonic() - start > tmo:
                raise TimeoutException()
        self.reading = False
        if data:
            return np.array(data)
        return None

    async def agenerate_pulse(self, npulses, delay_seconds, pin_output=None):
        pin = pin_output if pin_output is not None else self.pin_output
        delay_us = int(1e6 * delay_seconds)
        await self.interface.awrite(
            f"pulse {pin:d} {npulses:d} {delay_us:d}\n".encode("ascii")
        )
        while True:
            line = await self.interface.aread()
            line = line.decode("ascii").strip()
            if line:
                print(line)
                if line.startswith("single_pulse_generator FINISHED"):
                    break
            await asyncio.sleep(0.1)

    def configure_burst(self, freq, ncycles):
        """For compatibility with funcgen classes,

        .. code-block:: python

           arduino.configure_burst(freq, ncycles)
           arduino.trigger()

        is a equivalent to `arduino.generate_pulse(ncycles, 1/freq)`, except
        trigger() leave immediately.
        """
        self.freq = freq
        self.ncycles = ncycles

    def trigger(self, wait_completion=False):
        delay_us = int(1e6 / self.freq)
        self.interface.write(
            f"pulse {self.pin_output:d} {self.ncycles:d} {delay_us:d}\n"
        )
        while wait_completion and (
            line := self.interface.readline().decode("ascii").strip()
        ):
            print(line)
            if line.startswith("single_pulse_generator FINISHED"):
                break

    def configure_square(self, freq):
        delay_us = int(1e6 / freq)
        self.interface.write(f"continuous {self.pin_output:d} {delay_us:d}\n")

    def write_digital(self, pin_num, value):
        if pin_num < 2 or pin_num > 13:
            raise ValueError("Valid pins are between 2 and 13.")
        if value not in (0, 1):
            raise ValueError("Valid values are 0 or 1.")
        self.interface.write(f"write_digital {pin_num:d} {value:d}\n")
        start = monotonic()
        while line := self.interface.readline().decode("ascii").strip():
            print(line)
            if not line or line.startswith("write_digital FINISHED"):
                break
            if monotonic() - start > 5:
                print("Timeout reading from Arduino")
                break

    async def awrite_digital(self, pin_num, value):
        if pin_num < 2 or pin_num > 13:
            raise ValueError("Valid pins are between 2 and 13.")
        if value not in (0, 1):
            raise ValueError("Valid values are 0 or 1.")
        await self.interface.awrite(f"write_digital {pin_num:d} {value:d}\n")
        start = monotonic()
        while True:
            line = await self.interface.aread()
            line = line.decode("ascii").strip()
            print(line)
            if not line or line.startswith("digital_write"):
                break
            if monotonic() - start > 5:
                print("Timeout reading from Arduino")
                break
