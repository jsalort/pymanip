#! /usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division

import numpy as np

import PyDAQmx
import niScope

def read_analog(Scope_slot, Scope_channels, DAQmx_channels, volt_range, samples_per_chan, sample_rate):
    """
    Simultaneous NI Scope / NI DAQmx acquisition
    """

    # Configure the scope
    scope = niScope.Scope(Scope_slot)
    scope.ConfigureClock('VAL_PXI_CLOCK', 'VAL_NO_SOURCE', 'VAL_RTSI_0', True)
    scope.ConfigureHorizontalTiming(sampleRate=sample_rate, numPts=samples_per_chan)
    scope.ConfigureVertical(channelList=Scope_channels, voltageRange=volt_range)
    scope.ConfigureTrigger('Immediate')
    scope.ExportSignal('VAL_START_TRIGGER', 'Trigger start', 'VAL_RTSI_1')

    # Configure DAQmx channels
    task = PyDAQmx.Task()
    for chan in DAQmx_channels:
        task.CreateAIVoltageChan(chan, '', PyDAQmx.DAQmx_Val_Diff, -volt_range, volt_range,
                                 PyDAQmx.DAQmx_Val_Volts, None)
        task.SetChanAttribute(chan, PyDAQmx.DAQmx_AI_Coupling, PyDAQmx.DAQmx_Val_DC)
    
    task.CfgSampClkTiming('RTSI1', sample_rate, PyDAQmx.DAQmx_Val_Rising,
                          PyDAQmx.DAQmx_Val_FiniteSamps, samples_per_chan)
    task.CfgInputBuffer(samples_per_chan)

    # Start DAQmx task and initiate Scope acquisition
    task.StartTask()
    scope.InitiateAcquisition()

    # Read scope data
    data_scope = scope.Fetch(Scope_channels)
    length = scope.ActualRecordLength
    sampling = scope.ActualSamplingRate
    print('NI-Scope: {:} samples read at {:} Hz'.format(length, sampling))
    scope.close()

    # Read DAQmx data
    timeout = float(10*samples_per_chan / sample_rate)
    buffer_size_in_samps = int(samples_per_chan * nb_resources)
    data_daqmx = np.zeros((buffer_size_in_samps,), dtype=np.float64)
    samples_per_chan_read = PyDAQmx.int32()
    task.ReadAnalogF64(
        samples_per_chan, timeout, DAQmx_Val_GroupByChannel, data_daqmx,
        buffer_size_in_samps, byref(samples_per_chan_read), None)
    
    return (data_scope, data_daqmx)

if __name__ == '__main__':
    n = 100
    fe = 10e3
    (data_scope, data_daqmx) = read_analog('PXI1Slot3', '0', ('PXI1Slot4/ai2', ), 5.0, n, fe)
    t = np.arange(n)/fe
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(t, data_scope, 'ro')
    plt.plot(t, data_daqmx, 'bs')
    plt.show()
