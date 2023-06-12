"""Asynchronous Cryocon 24c
===========================

.. autoclass:: AsyncCryocon24c
   :members:
   :private-members:
   :show-inheritance:

"""

import fluidlab.instruments.multiplexer.cryocon_24c as fl_cryocon
from pymanip.aioinstruments.aioiec60488 import AsyncIEC60488
from pymanip.aioinstruments.aiosocket import AsyncSocketInstrument


class AsyncCryocon24c(AsyncIEC60488, AsyncSocketInstrument, fl_cryocon.Cryocon24c):
    pass


loop_output_power_to_power = fl_cryocon.loop_output_power_to_power
