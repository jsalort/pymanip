"""Asynchronous extension of Lauda chillers
===========================================

"""

import asyncio
import fluidlab.instruments.chiller.lauda as fl_lauda
from pymanip.aioinstruments.aiodrivers import AsyncDriver
from pymanip.aioinstruments.aiofeatures import AsyncValue

class AsyncLauda(AsyncDriver, fl_lauda.Lauda):
    async def __aenter__(self):
        await super().__aenter__()
        identification = await self.interface.aquery("TYPE\r")
        identification = identification.decode('ascii')
        if identification not in fl_lauda.Lauda.Models:
            if len(identification) > 0:
                raise fl_lauda.LaudaException("Unsupported model: " + identification)

            else:
                raise fl_Lauda.LaudaException(
                    "Cannot communicate with Lauda on " + str(self.port)
                )

        else:
            self.rom = fl_lauda.Lauda.Models[identification]
            print("Identification: " + identification)
        return self

class AsyncLaudaValue(AsyncValue, fl_lauda.LaudaValue):
    
    async def aget(self):
        result = await super().aget()
        result = result.decode('ascii')
        if len(result) < 3:
            raise fl_lauda.LaudaException("Erreur de communication")
        elif result.startswith("ERR"):
            raise fl_lauda.LaudaException("Erreur Lauda: " + result)
        else:
            return float(result)
    
    async def aset(self, value):
        command = self.command_set.format(value).encode("ascii")
        await self._interface.awrite(command)
        await asyncio.sleep(self.pause_instrument)
        confirmation = await self._interface.aread()
        confirmation = confirmation.decode('ascii')
        if confirmation != "OK":
            print(confirmation)
            raise fl_lauda.LaudaException("Erreur de communication")

class AsyncLaudaOnOffValue(AsyncLaudaValue, fl_lauda.LaudaOnOffValue):
    
    async def aget(self):
        if self._driver.rom in fl_lauda.LaudaOnOffValue.Supported_ROM:
            resultat = await super().aget()
            return True if (resultat == "1") else False
        else:
            return True
            
    async def aset(self, value):
        if value:
            await self._interface.write("START\r")
            await asyncio.sleep(self.pause_instrument)
            
class AsyncLaudaStatValue(AsyncValue, fl_lauda.LaudaStatValue):

    async def aget(self):
        result = await super().aget()
        if len(result) < 3:
            raise fl_lauda.LaudaException("Erreur de communication")

        elif result.startswith("ERR"):
            raise fl_lauda.LaudaException("Erreur Lauda: " + result)

        else:
            print(result)
            return {
                "overheat": True if (result[0] == "1") else False,
                "lowlevel": True if (result[1] == "1") else False,
                "pumperr": True if (result[2] == "1") else False,
                "controllererror1": True if (result[3] == "1") else False,
                "controllererror2": True if (result[4] == "1") else False,
            }
            
afeatures = [
    AsyncLaudaValue(
        "setpoint", command_get="IN_SP_00\r", command_set="OUT_SP_00 {:.2f}\r"
    ),
    AsyncLaudaStatValue("stat", command_get="STAT\r"),
    AsyncLaudaValue("temperature", command_get="IN_PV_00\r"),
    AsyncLaudaValue("waterlevel", command_get="IN_PV_05\r"),
    AsyncLaudaOnOffValue(),
]

AsyncLauda._build_class_with_features(afeatures)