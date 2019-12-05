"""PXI acquisition module (:mod:`pymanip.daq.PXI`)
==================================================

This module is an attempt to implement simultaneous DAQmx and Scope acquisition
on a PXI chassis.
It is not functionnal at the moment.

"""

import numpy as np

import PyDAQmx
import niScope


def read_analog(
    Scope_slot,
    Scope_channels,
    DAQmx_channels,
    volt_range,
    samples_per_chan,
    sample_rate,
):
    """
    Simultaneous NI Scope / NI DAQmx acquisition
    """

    # Configure the scope
    scope = niScope.Scope(Scope_slot)
    scope.ConfigureClock("VAL_PXI_CLOCK", "VAL_NO_SOURCE", "VAL_RTSI_0", True)
    scope.ConfigureHorizontalTiming(sampleRate=sample_rate, numPts=samples_per_chan)
    scope.ConfigureVertical(channelList=Scope_channels, voltageRange=volt_range)
    scope.ConfigureTrigger("Immediate")
    scope.ExportSignal(niScope.NISCOPE_VAL_REF_TRIGGER, "VAL_RTSI_1", "VAL_RTSI_1")
    sampling = scope.ActualSamplingRate
    if sampling != sample_rate:
        print("Warning: sample rate changed to", sampling)

    # Configure DAQmx channels
    task = PyDAQmx.Task()
    for chan in DAQmx_channels:
        task.CreateAIVoltageChan(
            chan,
            "",
            PyDAQmx.DAQmx_Val_Diff,
            -volt_range,
            volt_range,
            PyDAQmx.DAQmx_Val_Volts,
            None,
        )
        task.SetChanAttribute(chan, PyDAQmx.DAQmx_AI_Coupling, PyDAQmx.DAQmx_Val_DC)

    task.CfgDigEdgeStartTrig("RTSI1", PyDAQmx.DAQmx_Val_Rising)
    task.CfgSampClkTiming(
        "OnboardClock",
        sampling,
        PyDAQmx.DAQmx_Val_Rising,
        PyDAQmx.DAQmx_Val_FiniteSamps,
        samples_per_chan,
    )
    task.CfgInputBuffer(samples_per_chan)

    # Start DAQmx task and initiate Scope acquisition
    task.StartTask()
    scope.InitiateAcquisition()

    # Read scope data
    data_scope = scope.Fetch(Scope_channels)
    length = scope.ActualRecordLength
    print("NI-Scope: {:} samples read at {:} Hz".format(length, sampling))
    scope.close()

    # Read DAQmx data
    timeout = float(10 * samples_per_chan / sample_rate)
    buffer_size_in_samps = int(samples_per_chan * len(DAQmx_channels))
    data_daqmx = np.zeros((buffer_size_in_samps,), dtype=np.float64)
    samples_per_chan_read = PyDAQmx.int32()
    task.ReadAnalogF64(
        samples_per_chan,
        timeout,
        PyDAQmx.DAQmx_Val_GroupByChannel,
        data_daqmx,
        buffer_size_in_samps,
        PyDAQmx.byref(samples_per_chan_read),
        None,
    )
    print("DAQmx: %d samples read." % samples_per_chan_read.value)

    return (data_scope, data_daqmx)


if __name__ == "__main__":

    from pymanip.instruments import HP33120a

    source = HP33120a("GPIB0::10")
    f = source.freq.get()
    print("Source frequency is", f)

    n = 10000
    fe = 20 * f

    (data_scope, data_daqmx) = read_analog(
        "PXI1Slot3", "0", ("PXI1Slot4/ai2",), 5.0, n, fe
    )
    t = np.arange(n) / fe
    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(1000 * t, data_scope, "ro", label="Scope")
    plt.plot(1000 * t, data_daqmx, "bs", label="DAQ")
    plt.xlabel("t (ms)")
    plt.legend()
    plt.show()
