"""

Async Agilent 34970a: extension of fluidlab Agilent34970a class with asynchroneous scan/get/set

"""

from datetime import datetime
import numpy as np
import fluidlab.instruments.multiplexer.agilent_34970a as fl_agilent_34970a
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488


class AsyncAgilent34970aValue(fl_agilent_34970a.Agilent34970aValue):
    def _build_driver_class(self, Driver):

        super()._build_driver_class(Driver)

        async def aget(self, chanList, samplesPerChan=1, sampleRate=None, verbose=None):
            if verbose is None:
                verbose = samplesPerChan > 1
            result = await self._driver.ascan(
                chanList, self.function_name, samplesPerChan, sampleRate, verbose
            )
            if len(result) == 1:
                result = result[0]
            return result

        self.aget = aget.__get__(self, self.__class__)

        async def aset(self, channel, value, warn=True):
            if self.name == "vdc":
                await self._driver.awrite_vdc(channel, value)
            else:
                raise ValueError("Specified value cannot be written")

        self.aset = aset.__get__(self, self.__class__)


class AsyncAgilent34970a(AsyncIEC60488, fl_agilent_34970a.Agilent34970a):
    async def ascan(
        self, channelList, functionName, samplesPerChan, sampleRate, verbose=True
    ):

        try:
            # Checks if channelList is iterable
            numChans = len([x for x in channelList])
        except Exception:
            # If not, convert to 1-tuple
            channelList = (channelList,)
            numChans = 1

        # Max number of points: 50000
        if samplesPerChan * numChans > 50000:
            raise ValueError("Maximum number of samples is 50000 on Agilent 34970A")

        if samplesPerChan > 1:
            timeInterval = 1.0 / sampleRate
            if timeInterval < 1e-3:
                raise ValueError("The timer resolution of the Agilent 34970A is 1 ms")

        # Check that channel numbers are right
        badChans = [x for x in channelList if ((x < 100) and (x >= 400))]
        if len(badChans) > 0:
            raise ValueError(
                "Channels must be specified in the form scc, where s is "
                "the slot number (100, 200, 300), and cc is the channel "
                "number. For example, channel 10 on the slot 300 is referred "
                "to as 310."
            )

        # Set measurement type to desired function on specified channels
        msg = 'SENS:FUNC "' + functionName + '",(@'
        for i in range(numChans):
            msg = msg + str(channelList[i])
            if i < (numChans - 1):
                msg = msg + ","
            else:
                msg = msg + ")"
        await self.interface.awrite(msg)

        # Set range on specified channels
        for chan in channelList:
            if str(chan) in self.Range:
                # set channel to manual range
                await self.interface.awrite(
                    "SENS:"
                    + functionName
                    + ":RANG "
                    + str(self.Range[str(chan)])
                    + ",(@"
                    + str(chan)
                    + ")"
                )
            elif functionName != "TEMP":
                # set channel to Auto Range
                await self.interface.awrite(
                    "SENS:" + functionName + ":RANG:AUTO ON,(@" + str(chan) + ")"
                )

        # Set NPLC for specified channels
        for chan in channelList:
            if str(chan) in self.NPLC:
                # set NPLC to specified value
                await self.interface.awrite(
                    "SENS:"
                    + functionName
                    + ":NPLC "
                    + str(self.NPLC[str(chan)])
                    + ",(@"
                    + str(chan)
                    + ")"
                )
                if samplesPerChan > 1:
                    # warn if wrong value (50Hz line hard coded here)
                    tMoy = self.NPLC[str(chan)] / 50.0
                    if tMoy > 1.0 / sampleRate:
                        print(
                            "Warning: averaging for {:.1f} ms, and sample time is {:.1f} ms".format(
                                1000.0 * tMoy, 1000.0 / sampleRate
                            )
                        )
            elif samplesPerChan > 1:
                print("Warning: NPLC should be specified for acquisitions")

        # Set TK Type for specified channels (if TK channel and TkType defined)
        if functionName == "TEMP":
            for chan in channelList:
                if str(chan) in self.TkType:
                    # set Tk type to specified value
                    await self.interface.awrite(
                        "SENS:TEMP:TRAN:TC:TYPE "
                        + str(self.TkType[str(chan)])
                        + ",(@"
                        + str(chan)
                        + ")"
                    )

        # Setup scan list
        msg = "ROUT:SCAN (@"
        for i in range(numChans):
            msg = msg + str(channelList[i])
            if i < (numChans - 1):
                msg = msg + ","
            else:
                msg = msg + ")"
        await self.interface.awrite(msg)

        # Setup trigger and timer & Format
        if samplesPerChan > 1:
            await self.interface.awrite("TRIG:SOUR TIM")
            await self.interface.awrite("TRIG:TIM " + str(timeInterval))
            await self.interface.awrite("TRIG:COUN " + str(samplesPerChan))
            await self.interface.awrite("FORM:READ:TIME ON")
        else:
            await self.interface.awrite("TRIG:SOUR IMM")
            await self.interface.awrite("TRIG:COUN 1")
            await self.interface.awrite("FORM:READ:TIME OFF")
        await self.interface.awrite("FORM:READ:ALAR OFF")
        await self.interface.awrite("FORM:READ:CHAN OFF")
        await self.interface.awrite("FORM:READ:UNIT OFF")

        # Prepare status and event register
        await self.aclear_status()  # *CLS
        await self.event_status_enable_register.aset(1)  # *ESE 1
        await self.status_enable_register.aset(32)  # *SRE 32

        # Initiate scan and trigger Operation Complete event after completion
        await self.interface.awrite("INIT")
        if verbose:
            print(
                datetime.now().isoformat().replace("T", " ")
                + " - Acquisition initiated"
            )

        # Wait for Service Request (triggered by *OPC after the scan
        # is complete)
        await self.await_till_completion_of_operations()  # *OPC
        if sampleRate:
            tmo = 2 * int(1000 * samplesPerChan / sampleRate)
        else:
            tmo = 10000
        print("tmo =", tmo, "ms")
        await self.interface.await_for_srq(timeout=tmo)

        # Unassert SRQ
        await self.aclear_status()

        # Fetch data
        if verbose:
            print(datetime.now().isoformat().replace("T", " ") + " - Fetching data")
        data = await self.interface.aquery("FETCH?", verbose=verbose)

        # Parse data
        if samplesPerChan > 1:
            # timeStamp + value for each channel
            values = np.array([float(x) for x in data.split(",")])
            retval = values[::2], values[1::2]
        else:
            # expectedEntriesPerLine = numChans
            # only value for each channel
            retval = np.array([float(x) for x in data.split(",")])

        return retval


afeatures = [
    AsyncAgilent34970aValue("vdc", doc="DC Voltage", function_name="VOLT:DC"),
    AsyncAgilent34970aValue("vrms", doc="RMS Voltage", function_name="VOLT:AC"),
    AsyncAgilent34970aValue("temperature", doc="Temperature", function_name="TEMP"),
    AsyncAgilent34970aValue("ohm", doc="2-wire resistance", function_name="RES"),
    AsyncAgilent34970aValue("ohm_4w", doc="4-wire resistance", function_name="FRES"),
    AsyncAgilent34970aValue("idc", doc="DC Current", function_name="CURR:DC"),
]


AsyncAgilent34970a._build_class_with_features(afeatures)
