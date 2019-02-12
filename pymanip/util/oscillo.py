"""

Implements a live acquisition for NI cards

"""

import sys
import signal
import asyncio
import time

import numpy as np
import matplotlib.pyplot as plt

from nidaqmx import Task
from nidaqmx.constants import READ_ALL_AVAILABLE

class Oscillo:

    def __init__(self, channel_list, sampling, volt_range, trigger_level=None,
                 trigsource=0):
        self.channel_list = channel_list
        self.sampling = sampling
        self.volt_range = volt_range
        self.trigger_level = trigger_level
        self.trigger_source = trigsource
        plt.ion()
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
        self.running = False
        self.last_trigged = 0

    async def run_gui(self):
        while self.running:
            if time.monotonic()-self.last_trigged > 1024/self.sampling:
                self.ax.set_title('Waiting for trigger')
            self.fig.canvas.start_event_loop(0.5)
            await asyncio.sleep(0.05)
            if not plt.fignum_exists(self.fig.number):
                self.running = False

    async def run_acqui(self):
        loop = asyncio.get_event_loop()
        task = Task()
        for chan in self.channel_list:
            task.ai_channels.add_ai_voltage_chan(chan)
        task.timing.cfg_samp_clk_timing(self.sampling, samps_per_chan=1024)
        if self.trigger_level is not None:
            task.triggers.start_trigger.cfg_anlg_edge_start_trig(self.channel_list[self.trigger_source], trigger_level=self.trigger_level)
        t = np.arange(1024)/self.sampling
        if t[-1] < 1:
            t *= 1000
            unit = '[ms]'
        else:
            unit = '[s]'
        try:
            while self.running:
                task.start()
                await loop.run_in_executor(None,
                                           task.wait_until_done,
                                           10.0)
                data = task.read(READ_ALL_AVAILABLE)
                task.stop()
                self.last_trigged = time.monotonic()
                self.ax.cla()
                if len(self.channel_list) == 1:
                    self.ax.plot(t, data, '-')
                elif len(self.channel_list) > 1:
                    for d in data:
                        self.ax.plot(t, d, '-')
                if self.trigger_level is not None:
                    self.ax.plot([t[0], t[-1]], [self.trigger_level]*2, 'g--')
                self.ax.set_xlim([t[0], t[-1]])
                self.ax.set_title('Trigged!')
                self.ax.set_xlabel('t ' + unit)
        finally:
            task.close()

    def ask_exit(self, *args, **kwargs):
        self.running = False

    def run(self):
        loop = asyncio.get_event_loop()
        self.running = True
        if sys.platform == 'win32':
            signal.signal(signal.SIGINT, self.ask_exit)
        else:
            for signame in ('SIGINT', 'SIGTERM'):
                loop.add_signal_handler(getattr(signal, signame),
                                        self.ask_exit)

        loop.run_until_complete(asyncio.gather(self.run_gui(),
                                               self.run_acqui()))


if __name__ == '__main__':
    oscillo = Oscillo(['Dev2/ai0', 'Dev2/ai1'], 5e3, 10.0, trigger_level=2.0)
    oscillo.run()
