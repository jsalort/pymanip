"""

Implements a live acquisition for NI cards

"""

import sys
import signal
import asyncio
import time

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, TextBox, CheckButtons

from nidaqmx import Task
from nidaqmx.constants import READ_ALL_AVAILABLE
from nidaqmx.errors import DaqError

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
        # left, bottom, width, height
        self.ax = self.fig.add_axes([0.1,0.1,0.7,0.8])
        self.running = False
        self.last_trigged = 0
        self.ask_pause_acqui = False
        self.paused = False

        # Configure widgets
        ax_sampling = self.fig.add_axes([0.825, 0.825, 0.15, 0.075])
        self.textbox_sampling = TextBox(ax_sampling, label='',
                                        initial=f'{sampling:.1e}')
        self.textbox_sampling.on_submit(self.ask_sampling_change)
        label_sampling = ax_sampling.text(0, 1.25, 'Sampling')

        ax_enable_trigger = self.fig.add_axes([0.825, 0.65, 0.15, 0.15])
        self.checkbox_trigger = CheckButtons(ax_enable_trigger, ['Trigger'], [trigger_level is not None])
        self.checkbox_trigger.on_clicked(self.ask_trigger_change)

        ax_triggerlevel = self.fig.add_axes([0.825, 0.52, 0.15, 0.075])
        self.textbox_triggerlevel = TextBox(ax_triggerlevel, label='',
                                            initial=f'{trigger_level:.2f}' if trigger_level is not None else '1.0')
        self.textbox_triggerlevel.on_submit(self.ask_trigger_change)
        label_triggerlevel = ax_triggerlevel.text(0, 1.25, 'Level')
        
    def ask_trigger_change(self, label):
        changed = False
        trigger_enable, = self.checkbox_trigger.get_status()
        if trigger_enable:
            if self.trigger_level is None:
                changed = True
            try:
                self.trigger_level = float(self.textbox_triggerlevel.text)
                changed = True
            except ValueError:
                if self.trigger_level is not None:
                    self.textbox_triggerlevel.set_val(f'{self.trigger_level:.2f}')
                else:
                    self.textbox_triggerlevel.set_val('1.0')
                    changed = True
        else:
            if self.trigger_level is not None:
                changed = True
            self.trigger_level = None
        if changed:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(self.trigger_change(), loop=loop)

    async def pause_acqui(self):
        self.ask_pause_acqui = True
        while not self.paused:
            await asyncio.sleep(0.5)

    async def restart_acqui(self):
        self.ask_pause_acqui = False
        while self.paused:
            await asyncio.sleep(0.5)

    async def trigger_change(self):
        await self.pause_acqui()
        if self.trigger_level is not None:
            self.task.triggers.start_trigger.cfg_anlg_edge_start_trig(self.channel_list[self.trigger_source],
                                                                      trigger_level=self.trigger_level)
        else:
            self.task.triggers.start_trigger.disable_start_trig()
        await self.restart_acqui()

    async def sampling_change(self):
        await self.pause_acqui()
        try:
            self.task.timing.cfg_samp_clk_timing(self.sampling, samps_per_chan=1024)
        except DaqError:
            print('Invalid sampling frequency')
            self.ask_sampling_change(self.task.timing.samp_clk_max_rate)
            return
        self.figure_t_axis()
        await self.restart_acqui()
        
    def ask_sampling_change(self, sampling):
        try:
            self.sampling = float(sampling)
            changed = True
        except ValueError:
            print('Wrong value:', sampling)
            changed = False
        self.textbox_sampling.set_val(f'{self.sampling:.1e}')
        if changed:
            loop = asyncio.get_event_loop()
            asyncio.ensure_future(self.sampling_change(), loop=loop)

    def figure_t_axis(self):
        self.t = np.arange(1024)/self.sampling
        if self.t[-1] < 1:
            self.t *= 1000
            self.unit = '[ms]'
        else:
            self.unit = '[s]'

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
        self.task = Task()
        for chan in self.channel_list:
            self.task.ai_channels.add_ai_voltage_chan(chan)
        self.task.timing.cfg_samp_clk_timing(self.sampling, samps_per_chan=1024)
        if self.trigger_level is not None:
            self.task.triggers.start_trigger.cfg_anlg_edge_start_trig(self.channel_list[self.trigger_source], 
                                                                      trigger_level=self.trigger_level)
        self.figure_t_axis()
        try:
            while self.running:
                while self.ask_pause_acqui and self.running:
                    self.paused = True
                    await asyncio.sleep(0.5)
                self.paused = False
                if not self.running:
                    break
                self.task.start()
                done = False
                while not self.ask_pause_acqui and self.running:
                    try:
                        await loop.run_in_executor(None,
                                                   self.task.wait_until_done,
                                                   1.0)
                    except DaqError:
                        continue
                    done = True
                    break
                if done:
                    data = self.task.read(READ_ALL_AVAILABLE)
                    self.last_trigged = time.monotonic()
                self.task.stop()
                if not done:
                    continue
                self.ax.cla()
                if len(self.channel_list) == 1:
                    self.ax.plot(self.t, data, '-')
                elif len(self.channel_list) > 1:
                    for d in data:
                        self.ax.plot(self.t, d, '-')
                if self.trigger_level is not None:
                    self.ax.plot([self.t[0], self.t[-1]], [self.trigger_level]*2, 'g--')
                self.ax.set_xlim([self.t[0], self.t[-1]])
                self.ax.set_title('Trigged!')
                self.ax.set_xlabel('t ' + self.unit)
        finally:
            self.task.close()

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
