import tkinter
from nidaqmx.system import system, device


class ChannelSelector:

    def __init__(self):
        self.sys = system.System()
        self.device_list = dict()
        for devname in self.sys.devices.device_names:
            dev = device.Device(devname)
            description = dev.product_type
            if description.startswith('PXI'):
                description = f'PXI {dev.pxi_chassis_num:d} ' \
                              f'Slot {dev.pxi_slot_num:d} ' \
                              f'({dev.product_type:})'
            elif description.startswith('PCI'):
                description = f'{dev.product_type:} ' \
                              f'({dev.pci_bus_num:} ' \
                              f'{dev.pci_dev_num:})'
            self.device_list[description] = dev.ai_physical_chans.channel_names

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
        return [chan for chan in values if values[chan].get()]
