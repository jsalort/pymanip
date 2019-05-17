#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division

import numpy as np

try:
    from clint.textui import colored
except ImportError:

    def colored(string):
        return string


import ctypes
import fluidlab.daq.daqmx as daqmx
from fluidlab.daq.daqmx import write_analog
import six


class DAQDevice(object):
    """
    This class is represents a DAQmx device
    """

    @staticmethod
    def list_connected_devices():
        try:
            from PyDAQmx import DAQmxGetSystemInfoAttribute, DAQmx_Sys_DevNames

            bufsize = 1024
            buf = ctypes.create_string_buffer(bufsize)
            DAQmxGetSystemInfoAttribute(DAQmx_Sys_DevNames, ctypes.byref(buf), bufsize)
            return [DAQDevice(s.strip().decode("ascii")) for s in buf.value.split(b",")]
        except ImportError:
            print("Cannot list connected devices.")
            return None
            pass

    def __init__(self, device_name):
        self.device_name = device_name

    @property
    def product_category(self):
        try:
            from PyDAQmx import (
                DAQmxGetDevProductCategory,
                DAQmx_Val_MSeriesDAQ,
                DAQmx_Val_XSeriesDAQ,
                DAQmx_Val_ESeriesDAQ,
                DAQmx_Val_SSeriesDAQ,
                DAQmx_Val_BSeriesDAQ,
                DAQmx_Val_SCSeriesDAQ,
                DAQmx_Val_USBDAQ,
                DAQmx_Val_AOSeries,
                DAQmx_Val_DigitalIO,
                DAQmx_Val_TIOSeries,
                DAQmx_Val_DynamicSignalAcquisition,
                DAQmx_Val_Switches,
                DAQmx_Val_CompactDAQChassis,
                DAQmx_Val_CSeriesModule,
                DAQmx_Val_SCXIModule,
                DAQmx_Val_SCCConnectorBlock,
                DAQmx_Val_SCCModule,
                DAQmx_Val_NIELVIS,
                DAQmx_Val_NetworkDAQ,
                DAQmx_Val_SCExpress,
                DAQmx_Val_Unknown,
            )

            category = ctypes.c_int32(DAQmx_Val_Unknown)
            DAQmxGetDevProductCategory(self.device_name, ctypes.byref(category))
            return {
                DAQmx_Val_MSeriesDAQ: "M Series DAQ",
                DAQmx_Val_XSeriesDAQ: "X Series DAQ",
                DAQmx_Val_ESeriesDAQ: "E Series DAQ",
                DAQmx_Val_SSeriesDAQ: "S Series DAQ",
                DAQmx_Val_BSeriesDAQ: "B Series DAQ",
                DAQmx_Val_SCSeriesDAQ: "SC Series DAQ",
                DAQmx_Val_USBDAQ: "USB DAQ",
                DAQmx_Val_AOSeries: "AO Series",
                DAQmx_Val_DigitalIO: "Digital I/O",
                DAQmx_Val_TIOSeries: "TIO Series",
                DAQmx_Val_DynamicSignalAcquisition: "Dynamic Signal Acquisition",
                DAQmx_Val_Switches: "Switches",
                DAQmx_Val_CompactDAQChassis: "CompactDAQ chassis",
                DAQmx_Val_CSeriesModule: "C Series I/O module",
                DAQmx_Val_SCXIModule: "SCXI module",
                DAQmx_Val_SCCConnectorBlock: "SCC Connector Block",
                DAQmx_Val_SCCModule: "SCC Module",
                DAQmx_Val_NIELVIS: "NI ELVIS",
                DAQmx_Val_NetworkDAQ: "Network DAQ",
                DAQmx_Val_SCExpress: "SC Express",
                DAQmx_Val_Unknown: "Unknown by DAQmx",
            }.get(category.value, "Unknown")
        except ImportError:
            return None

    @property
    def product_type(self):
        from PyDAQmx import DAQmxGetDevProductType

        bufsize = 1024
        buf = ctypes.create_string_buffer(bufsize)
        DAQmxGetDevProductType(self.device_name, buf, bufsize)
        return buf.value.decode("ascii")

    @property
    def product_num(self):
        from PyDAQmx import DAQmxGetDevProductNum

        num = ctypes.c_uint32(0)
        DAQmxGetDevProductNum(self.device_name, ctypes.byref(num))
        return num.value

    @property
    def ai_chans(self):
        from PyDAQmx import DAQmxGetDevAIPhysicalChans

        bufsize = 2048
        buf = ctypes.create_string_buffer(bufsize)
        DAQmxGetDevAIPhysicalChans(self.device_name, buf, bufsize)
        chans = [s.strip().decode("ascii") for s in buf.value.split(b",")]
        if chans == [""]:
            chans = []
        return chans

    @property
    def ao_chans(self):
        from PyDAQmx import DAQmxGetDevAOPhysicalChans

        bufsize = 2048
        buf = ctypes.create_string_buffer(bufsize)
        DAQmxGetDevAOPhysicalChans(self.device_name, buf, bufsize)
        chans = [s.strip().decode("ascii") for s in buf.value.split(b",")]
        if chans == [""]:
            chans = []
        return chans

    @property
    def di_lines(self):
        from PyDAQmx import DAQmxGetDevDILines

        bufsize = 2048
        buf = ctypes.create_string_buffer(bufsize)
        DAQmxGetDevDILines(self.device_name, buf, bufsize)
        chans = [s.strip().decode("ascii") for s in buf.value.split(b",")]
        if chans == [""]:
            chans = []
        return chans

    @property
    def di_ports(self):
        from PyDAQmx import DAQmxGetDevDIPorts

        bufsize = 2048
        buf = ctypes.create_string_buffer(bufsize)
        DAQmxGetDevDIPorts(self.device_name, buf, bufsize)
        chans = [s.strip().decode("ascii") for s in buf.value.split(b",")]
        if chans == [""]:
            chans = []
        return chans

    @property
    def do_lines(self):
        from PyDAQmx import DAQmxGetDevDOLines

        bufsize = 2048
        buf = ctypes.create_string_buffer(bufsize)
        DAQmxGetDevDOLines(self.device_name, buf, bufsize)
        chans = [s.strip().decode("ascii") for s in buf.value.split(b",")]
        if chans == [""]:
            chans = []
        return chans

    @property
    def do_ports(self):
        from PyDAQmx import DAQmxGetDevDOPorts

        bufsize = 2048
        buf = ctypes.create_string_buffer(bufsize)
        DAQmxGetDevDOPorts(self.device_name, buf, bufsize)
        chans = [s.strip().decode("ascii") for s in buf.value.split(b",")]
        if chans == [""]:
            chans = []
        return chans

    @property
    def bus_type(self):
        from PyDAQmx import (
            DAQmxGetDevBusType,
            DAQmx_Val_PCI,
            DAQmx_Val_PXI,
            DAQmx_Val_SCXI,
            DAQmx_Val_PCCard,
            DAQmx_Val_USB,
            DAQmx_Val_Unknown,
        )

        t = ctypes.c_int32(0)
        DAQmxGetDevBusType(self.device_name, ctypes.byref(t))
        return {
            DAQmx_Val_PCI: "PCI",
            DAQmx_Val_PXI: "PXI",
            DAQmx_Val_SCXI: "SCXI",
            DAQmx_Val_PCCard: "PCCard",
            DAQmx_Val_USB: "USB",
            DAQmx_Val_Unknown: "DAQmx unknown",
        }.get(t.value, "Unknown")

    @property
    def pci_busnum(self):
        from PyDAQmx import DAQmxGetDevPCIBusNum

        num = ctypes.c_uint32(0)
        DAQmxGetDevPCIBusNum(self.device_name, ctypes.byref(num))
        return num.value

    @property
    def pci_devnum(self):
        from PyDAQmx import DAQmxGetDevPCIDevNum

        num = ctypes.c_uint32(0)
        DAQmxGetDevPCIDevNum(self.device_name, ctypes.byref(num))
        return num.value

    @property
    def pxi_chassisnum(self):
        from PyDAQmx import DAQmxGetDevPXIChassisNum

        num = ctypes.c_uint32(0)
        DAQmxGetDevPXIChassisNum(self.device_name, ctypes.byref(num))
        return num.value

    @property
    def pxi_slotnum(self):
        from PyDAQmx import DAQmxGetDevPXISlotNum

        num = ctypes.c_uint32(0)
        DAQmxGetDevPXISlotNum(self.device_name, ctypes.byref(num))
        return num.value

    @property
    def location(self):
        from PyDAQmx import DAQError

        bus = self.bus_type
        if bus == "PCI":
            desc = "PCI {:d}, {:d}".format(self.pci_busnum, self.pci_devnum)
        elif bus == "PXI":
            try:
                desc = "PXI chassis {:d} slot {:d}".format(
                    self.pxi_chassisnum, self.pxi_slotnum
                )
            except DAQError:
                # Si le chassis n'est pas identifié alors DAQmx ne peut pas
                # renvoyer les informations, et une exception est levée
                desc = "PXI (unidentified)"
                pass
        else:
            desc = bus
        return desc


def print_connected_devices():
    for device in DAQDevice.list_connected_devices():
        print(
            "**",
            device.device_name,
            "(" + device.product_type + ") on",
            device.location,
            "**",
        )
        print("Analog input  :", device.ai_chans)
        print("Analog output :", device.ao_chans)


# Ici read_analog est verbose=True par défaut contrairement à fluidlab
# et on ajoute une fonction "autoset" si volt_min, volt_max sont None
def read_analog(
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
    """

    Reads signal from analog input.

    resources_names: names from MAX (Dev1/ai0)
    terminal_config: "Diff", "RSE", "NRSE"
    volt_min, volt_max: channel range

    If the channel range is not specified, a 5.0 seconds samples will first be acquired
    to determine appropriate channel range.

    """

    # Les type checks ci-dessous ne sont pas très pythoniques
    # mais nécessaire parce que PyDAQmx est une passerelle vers le C
    # et il y a des sous-entendus de type.

    # Ensure that samples_per_chan is integer
    if not isinstance(samples_per_chan, int):
        samples_per_chan = int(samples_per_chan)

    # Ensure resource_names is str or list of str
    if isinstance(resource_names, six.string_types):
        num_channels = 1
        resource_names = str(resource_names)
    else:
        num_channels = len(resource_names)
        resource_names = [str(r) for r in resource_names]

    # If no range is provided, take a 5s sample
    if volt_min is None or volt_max is None:
        print("Sampling 5s data to determine channel range")
        if num_channels == 1:
            volt_min = -10.0
            volt_max = 10.0
        else:
            volt_min = [-10.0] * num_channels
            volt_max = [10.0] * num_channels

        data = daqmx.read_analog(
            resource_names,
            terminal_config,
            volt_min,
            volt_max,
            samples_per_chan=50000,
            sample_rate=10e3,
            coupling_types=coupling_types,
            verbose=False,
        )
        if num_channels == 1:
            volt_range = np.max(np.abs(data)) * 1.25
            volt_min = -volt_range
            volt_max = volt_range
        else:
            for chan in range(num_channels):
                volt_range = np.max(np.abs(data[chan])) * 1.25
                volt_min[chan] = -volt_range
                volt_max[chan] = volt_range
                print(
                    "Channel", chan, "min max:", np.min(data[chan]), np.max(data[chan])
                )

    # Run fluidlab daqmx.read_analog with verbose=True by default
    data = daqmx.read_analog(
        resource_names,
        terminal_config,
        volt_min,
        volt_max,
        samples_per_chan,
        sample_rate,
        coupling_types,
        output_filename,
        verbose,
    )

    # If verbose, check that voltage range has not been reached and issue a warning otherwise
    if verbose:
        if num_channels == 1:
            channel_range = np.max([np.abs(volt_min), np.abs(volt_max)])
            if np.max(np.abs(data)) >= channel_range:
                colored.red("WARNING: channel range too small!")
        else:
            for chan in range(num_channels):
                try:
                    channel_range = np.max(
                        [np.abs(volt_min[chan]), np.abs(volt_max[chan])]
                    )
                except TypeError:
                    channel_range = np.max([np.abs(volt_min), np.abs(volt_max)])
                    pass

                if np.max(np.abs(data[chan])) >= channel_range:
                    colored.red(
                        "WARNING: channel range is too small for channel "
                        + resource_names[chan]
                    )

    return data


# def write_analog(resource_names, sample_rate, signals, blocking=True):
#    return daqmx.write_analog(resource_names, sample_rate, signals, blocking)


def write_analog_end_task(task, timeout=0.0):
    daqmx.write_analog_end_task(task, timeout)


def measure_freq(resource_name, freq_min=1, freq_max=1000):
    return daqmx.measure_freq(resource_name, freq_min, freq_max)
