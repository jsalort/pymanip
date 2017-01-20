"""
This module implements handy wrappers around the NI-Scope API
"""

import numpy as np
from niScope import Scope

try:
    from clint.textui import colored
except ImportError:
    def colored(string):
        return string

def read_analog(scope_name, channelList="0", volt_range=10.0,
                samples_per_chan=100, sample_rate=1000.0, coupling_type='DC'):
    """
    Scope analog read
    """
    scope = Scope(scope_name)
    scope.ConfigureHorizontalTiming(sampleRate=sample_rate, numPts=samples_per_chan)
    scope.ConfigureVertical(channelList=channelList, voltageRange=volt_range)
    scope.ConfigureTrigger('Immediate')
    sampling = scope.ActualSamplingRate
    if sampling != sample_rate:
        print(colored.red('Warning: sampling frequency changed to {:} Hz.'.format(sampling)))
    scope.InitiateAcquisition()
    data = scope.Fetch(channelList)
    length = scope.ActualRecordLength
    scope.close()
    return data
    
