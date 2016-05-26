#! /usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from clint.textui import colored

import fluidlab.instruments.daq.daqmx as daqmx

# Ici read_analog est verbose=True par défaut contrairement à fluidlab
# et on ajoute une fonction "autoset" si volt_min, volt_max sont None
def read_analog(resource_names, terminal_config, volt_min=None, volt_max=None,
                                samples_per_chan=1, sample_rate=1, coupling_types='DC',
                                output_filename=None, verbose=True):
    """

    Reads signal from analog input.

    resources_names: names from MAX (Dev1/ai0)
    terminal_config: "Diff", "RSE", "NRSE"
    volt_min, volt_max: channel range

    If the channel range is not specified, a 5.0 seconds samples will first be acquired
    to determine appropriate channel range.

    """
    
    # Ensure that samples_per_chan is integer
    if not isinstance(samples_per_chan, int):
        samples_per_chan = int(samples_per_chan)

    if isinstance(resource_names, str):
        num_channels = 1
    else:
        num_channels = len(resource_names)

    # If no range is provided, take a 5s sample
    if volt_min is None or volt_max is None:
        print 'Sampling 5s data to determine channel range'
        if num_channels == 1:
            volt_min = -10.0
            volt_max = 10.0
        else:
            volt_min = [-10.0]*num_channels
            volt_max = [10.0]*num_channels

        data = daqmx.read_analog(resource_names, terminal_config, volt_min, volt_max,
                                 samples_per_chan=50000,
                                 sample_rate=10e3,
                                 coupling_types=coupling_types,
                                 verbose=False)
        if num_channels == 1:
            volt_range = np.max(np.abs(data))*1.25
            volt_min = -volt_range
            volt_max = volt_range
        else:
            for chan in range(num_channels):
                volt_range = np.max(np.abs(data[chan]))*1.25
                volt_min[chan] = -volt_range
                volt_max[chan] = volt_range
                print 'Channel', chan, 'min max:', np.min(data[chan]), np.max(data[chan])

    # Run fluidlab daqmx.read_analog with verbose=True by default
    data = daqmx.read_analog(resource_names, terminal_config, volt_min, volt_max,
                            samples_per_chan, sample_rate, coupling_types,
                            output_filename, verbose)

    # If verbose, check that voltage range has not been reached and issue a warning otherwise
    if verbose:
        if num_channels == 1:
            channel_range = np.max([np.abs(volt_min), np.abs(volt_max)])
            if np.max(np.abs(data)) >= channel_range:
                colored.red('WARNING: channel range too small!')
        else:
            for chan in range(num_channels):
                try:
                    channel_range = np.max([np.abs(volt_min[chan]), np.abs(volt_max[chan])])
                except TypeError:
                    channel_range = np.max([np.abs(volt_min), np.abs(volt_max)])
                    pass

                if np.max(np.abs(data[chan])) >= channel_range:
                    colored.red('WARNING: channel range is too small for channel ' + resource_names[chan])

    return data


def write_analog(resource_names, sample_rate, signals, blocking=True):
    return daqmx.write_analog(resource_names, sample_rate, signals, blocking)

def write_analog_end_task(task, timeout=0.):
    daqmx.write_analog_end_task(task, timeout)

def measure_freq(resource_name, freq_min=1, freq_max=1000):
    return daqmx.measure_freq(resource_name, freq_min, freq_max)
