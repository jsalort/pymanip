"""Asynchronous Instrument features (:mod:`pymanip.aioinstruments.aiofeatures`)
===============================================================================

Asynchronous extension of fluidlab instrument features. The main difference is that they
define :meth:`aget` and :meth:`aset` co-routine methods. The original :meth:`get` and
:meth:`set` are not overridden, and may still be used.

.. autoclass:: AsyncWriteCommand
   :members:
   :private-members:

.. autoclass:: AsyncQueryCommand
   :members:
   :private-members:

.. autoclass:: AsyncValue
   :members:
   :private-members:

.. autoclass:: AsyncNumberValue
   :members:
   :private-members:

.. autoclass:: AsyncFloatValue
   :members:
   :private-members:

.. autoclass:: AsyncBoolValue
   :members:
   :private-members:

.. autoclass:: AsyncIntValue
   :members:
   :private-members:

.. autoclass:: AsyncRegisterValue
   :members:
   :private-members:

"""

import asyncio
import fluidlab.instruments.features as flfeatures


class AsyncWriteCommand(flfeatures.WriteCommand):
    def _build_driver_class(self, Driver):
        super()._build_driver_class(Driver)
        command_str = self.command_str

        async def func(self):
            await self._interface.awrite(command_str)

        func.__doc__ = self.__doc__
        setattr(Driver, self._name, func)


class AsyncQueryCommand(flfeatures.QueryCommand):
    def _build_driver_class(self, Driver):
        super()._build_driver_class(Driver)

        command_str = self.command_str

        if self.parse_result is None:

            async def func(self):
                return await self._interface.aquery(command_str)

        else:

            async def func(self):
                r = await self._interface.aquery(command_str)
                return self.parse_result(r)

        func.__doc__ = self.__doc__
        setattr(Driver, self._name, func)


class AsyncValue(flfeatures.Value):
    async def aget(self, channel=0):
        if isinstance(channel, list) or isinstance(channel, tuple):
            return [await self.aget(c) for c in channel]

        if self.pause_instrument > 0:
            await asyncio.sleep(self.pause_instrument)

        command = self.command_get
        if self.channel_argument:
            command = command.format(channel=channel)
        if self.pause_instrument > 0:
            r = await self._interface.aquery(command, time_delay=self.pause_instrument)
        else:
            r = await self._interface.aquery(command)
        result = self._convert_from_str(r)
        self._check_value(result)
        return result

    async def aset(self, value, channel=0):
        if self.pause_instrument > 0:
            await asyncio.sleep(self.pause_instrument)
        self._check_value(value)
        if self.channel_argument:
            # here we don't call _convert_as_str to allow the user to choose
            # the desired format in the command_set string
            command = self.command_set.format(channel=channel, value=value)
        else:
            command = self.command_set + " " + self._convert_as_str(value)
        await self._interface.awrite(command)
        if self.check_instrument_value_after_set:
            self._check_instrument_value(value)


class AsyncNumberValue(AsyncValue, flfeatures.NumberValue):
    pass


class AsyncFloatValue(AsyncNumberValue, flfeatures.FloatValue):
    pass


class AsyncBoolValue(AsyncValue, flfeatures.BoolValue):
    pass


class AsyncIntValue(AsyncNumberValue, flfeatures.IntValue):
    pass


class AsyncRegisterValue(AsyncNumberValue, flfeatures.RegisterValue):
    async def aget_as_number(self):
        value = await self._interface.aquery(self.command_get)
        self._check_value(value)
        return value

    async def aget(self):
        number = await self.aget_as_number()
        return self.compute_dict_from_number(number)

    async def aset(self, value):
        if isinstance(value, dict):
            value = self.compute_number_from_dict(value)

        self._check_value(value)
        await self._interface.awrite(self.command_set + f" {value}")
