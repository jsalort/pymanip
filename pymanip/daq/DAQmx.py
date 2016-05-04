#! /usr/bin/env python
# -*- coding: utf-8 -*-

import fluidlab.instruments.daq.daqmx as daqmx

# Ici read_analog est verbose=True par défaut contrairement à fluidlab
def read_analog(resource_names, terminal_config, volt_min, volt_max,
                samples_per_chan=1, sample_rate=1, coupling_types='DC',
                output_filename=None, verbose=True):
    return daqmx.read_analog(resource_names, terminal_config, volt_min, volt_max,
                samples_per_chan, sample_rate, coupling_types,
                output_filename, verbose)

def write_analog(resource_names, sample_rate, signals, blocking=True):
    return daqmx.write_analog(resource_names, sample_rate, signals, blocking)

def write_analog_end_task(task, timeout=0.):
    daqmx.write_analog_end_task(task, timeout)

def measure_freq(resource_name, freq_min=1, freq_max=1000):
    return daqmx.measure_freq(resource_name, freq_min, freq_max)
