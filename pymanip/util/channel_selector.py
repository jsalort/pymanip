import tkinter

from pymanip.aiodaq.daqmx import get_device_list as daqmx_get_devices
from pymanip.aiodaq.scope import get_device_list as scope_get_devices

class ChannelSelector:

    def __init__(self):
        self.daqmx_device_list = daqmx_get_devices()
        self.scope_device_list = scope_get_devices(self.daqmx_device_list)
        self.device_list = self.daqmx_device_list.copy()
        self.device_list.update(self.scope_device_list)
        self.channel_backend = dict()
        for name, devlist in self.daqmx_device_list.items():
            for dev in devlist:
                self.channel_backend[dev] = 'daqmx'
        for name, devlist in self.scope_device_list.items():
            for dev in devlist:
                self.channel_backend[dev] = 'scope'


    def print_channel_list(self):
        for name, devlist in self.device_list.items():
            print(name)
            print('-'*len(name))
            print(devlist)

    def gui_select(self):
        master = tkinter.Tk()
        ii = 0
        tkinter.Label(master,
                      text='Choose channels').grid(row=ii,
                                                   sticky=tkinter.W)
        ii += 1
        values = dict()
        for card, devlist in self.device_list.items():
            for dev in devlist:
                values[dev] = tkinter.IntVar()
                tkinter.Checkbutton(master,
                                    text=dev,
                                    variable=values[dev]).grid(row=ii,
                                                               sticky=tkinter.W)
                ii += 1
        tkinter.Button(master, text='OK',
                       command=master.quit).grid(row=ii,
                                                 sticky=tkinter.W)
        tkinter.mainloop()
        master.destroy()
        selected_channels = [chan for chan in values if values[chan].get()]
        selected_backends = [self.channel_backend[chan] for chan in selected_channels]
        if not all([b == selected_backends[0] for b in selected_backends]):
            raise ValueError('Channels from different backends were selected !')
        return selected_backends[0], selected_channels
