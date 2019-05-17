"""
This module implements handy wrappers around the NI-Scope API
"""

from __future__ import print_function, unicode_literals, division

from niScope import Scope
from platform import platform
import time
import pymanip.mytime as MI
from collections import Iterable

try:
    from clint.textui import colored
except ImportError:

    def colored(string):
        return string


def print_horodateur(samples_per_chan, sample_rate):
    if platform().startswith("Windows"):
        dateformat = "%A %d %B %Y - %X (%z)"
    else:
        dateformat = "%A %e %B %Y - %H:%M:%S (UTC%z)"
    starttime = time.time()
    starttime_str = time.strftime(dateformat, time.localtime(starttime))
    endtime = starttime + samples_per_chan / sample_rate
    endtime_str = time.strftime(dateformat, time.localtime(endtime))
    print("Scope: Starting acquisition: " + starttime_str)
    print(
        "       Expected duration: %.2f min" % (samples_per_chan / (60.0 * sample_rate))
    )
    print("       Expected end time: " + endtime_str)


def read_analog(
    scope_name,
    channelList="0",
    volt_range=10.0,
    samples_per_chan=100,
    sample_rate=1000.0,
    coupling_type="DC",
):
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
    sample_rate = float(sample_rate)
    channelList = str(channelList)
    numChannels = len(channelList.split(","))
    if isinstance(volt_range, Iterable):
        volt_range = [float(v) for v in volt_range]
    else:
        volt_range = float(volt_range)
        if numChannels > 1:
            volt_range = [volt_range] * numChannels

    scope = Scope(scope_name)
    print("Scope:", scope_name)
    scope.ConfigureHorizontalTiming(sampleRate=sample_rate, numPts=samples_per_chan)
    scope.NumRecords = 1
    if numChannels == 1:
        scope.ConfigureVertical(channelList=channelList, voltageRange=volt_range)
    else:
        for chan, v in zip(channelList.split(","), volt_range):
            print("Scope: setting chan {:s} voltage range to {:}.".format(chan, v))
            scope.ConfigureVertical(channelList=chan, voltageRange=v)
            actualRange = scope.ActualVoltageRange(chan)
            if actualRange != volt_range:
                print(
                    "Scope: actual range for chan {:s} is {:}".format(chan, actualRange)
                )
    scope.ConfigureTrigger("Immediate")
    sampling = scope.ActualSamplingRate
    length = scope.ActualRecordLength
    print_horodateur(length, sampling)
    if sampling != sample_rate:
        print(
            colored.red(
                "Warning: sampling frequency changed to {:} Hz.".format(sampling)
            )
        )
    if length != samples_per_chan:
        print(
            colored.red("Warning: record length changed to {:d} points.".format(length))
        )
    if numChannels == 1:
        vRange = scope.ActualVoltageRange(channelList)
        if vRange != volt_range:
            print(colored.red("Warning: actual voltage range is {:} V.".format(vRange)))
    else:
        for chan, v in zip(channelList.split(","), volt_range):
            vv = scope.ActualVoltageRange(chan)
            if vv != v:
                print(
                    colored.red(
                        "Warning: actual range for channel {:s} is {:} V.".format(
                            chan, vv
                        )
                    )
                )
    scope.InitiateAcquisition()
    duration = samples_per_chan / sampling
    MI.sleep(duration)
    data = scope.Fetch(channelList, timeout=duration)
    (l, c) = data.shape
    print("Scope: {:d} samples read.".format(l))
    scope.close()

    return tuple(data[:, i] for i in range(numChannels))
