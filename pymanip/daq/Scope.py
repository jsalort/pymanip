"""
This module implements handy wrappers around the NI-Scope API
"""

from __future__ import print_function, unicode_literals, division

import numpy as np
from niScope import Scope
from platform import platform
import time
import pymanip.mytime as MI

try:
    from clint.textui import colored
except ImportError:
    def colored(string):
        return string

def print_horodateur(samples_per_chan, sample_rate):
    if platform().startswith('Windows'):
        dateformat = '%A %d %B %Y - %X (%z)'
    else:
        dateformat = '%A %e %B %Y - %H:%M:%S (UTC%z)'
    starttime = time.time()
    starttime_str = time.strftime(dateformat, time.localtime(starttime))
    endtime = starttime+samples_per_chan/sample_rate
    endtime_str = time.strftime(dateformat, time.localtime(endtime))
    print("Scope: Starting acquisition: " + starttime_str)
    print("       Expected duration: %.2f min" % (samples_per_chan/(60.0*sample_rate)))
    print("       Expected end time: " + endtime_str)

def read_analog(scope_name, channelList="0", volt_range=10.0,
                samples_per_chan=100, sample_rate=1000.0, coupling_type='DC'):
    """
    Scope analog read.

    Input
    =====

        scope_name: name of the NI-Scope device (e.g. 'Dev3')
        channelList: comma-separated string of channel number (e.g. "0")
        volt_range
        samples_per_scan
        sample_rate: for 5922 60e6/n avec n entre 4 et 1200
        coupling_type: 'DC', 'AC', 'GND'
    """
    
    # Make sure scalars have the correct type, as it will otherwise
    # fail to convert to the corresponding Vi types
    samples_per_chan = int(samples_per_chan)
    volt_range = float(volt_range)
    sample_rate = float(sample_rate)
    channelList = str(channelList)
    numChannels = len(channelList.split(","))

    scope = Scope(scope_name)
    print('Scope:', scope_name)
    scope.ConfigureHorizontalTiming(sampleRate=sample_rate, numPts=samples_per_chan)
    scope.ConfigureVertical(channelList=channelList, voltageRange=volt_range)
    scope.ConfigureTrigger('Immediate')
    print_horodateur(samples_per_chan, sample_rate)
    sampling = scope.ActualSamplingRate
    if sampling != sample_rate:
        print(colored.red('Warning: sampling frequency changed to {:} Hz.'.format(sampling)))
    vRange = scope.ActualVoltageRange
    if vRange != volt_range:
        print(colored.red('Warning: actual voltage range is {:} V.'.format(vRange)))

    scope.InitiateAcquisition()
    duration = samples_per_chan/sampling
    MI.sleep(duration)
    data = scope.Fetch(channelList, timeout=duration/10)
    length = scope.ActualRecordLength
    print('Scope: {:d} samples read.'.format(length))
    scope.close()

    return tuple(data[:,i] for i in range(numChannels))
    
