"""

Asynchroneous version of fluidlab.interfaces

"""

import warnings
import asyncio
import fluidlab.interfaces as flinter
import functools


class AsyncQueryInterface(flinter.QueryInterface):
    def __init__(self):
        """
        If lock is given, it is acquired before any operation on the board.
        """

        super().__init__()
        self.loop = asyncio.get_event_loop()
        self.lock = (
            asyncio.Lock()
        )  # dummy lock since it is not shared by another interface,
        # but it prevents the same device to concurrently talk

    def __str__(self):
        return "Async" + super().__str__()

    def __repr__(self):
        return str(self)

    async def __aenter__(self):
        async with self.lock:
            return await self.loop.run_in_executor(None, self.__enter__)

    async def __aexit__(self, type_, value, tb):
        async with self.lock:
            await self.loop.run_in_executor(None, self.__exit__, type_, value, tb)

    async def _awrite(self, *args, **kwargs):
        async with self.lock:
            await self.loop.run_in_executor(
                None, self._write, *args, **kwargs
            )  # must be rewritten if necessary in concrete class

    async def _aread(self, *args, **kwargs):
        async with self.lock:
            await self.loop.run_in_executor(None, self._read, *args, **kwargs)

    async def _aquery(self, command, time_delay=0.1, **kwargs):
        async with self.lock:
            if hasattr(self, "_query"):
                query_func = functools.partial(
                    self.query, command, time_delay=time_delay, **kwargs
                )
                return await self.loop.run_in_executor(None, query_func)
            else:
                await self.awrite(command)
                await asyncio.sleep(time_delay)
                return await self.aread(**kwargs)

    async def awrite(self, *args, **kwargs):
        if not self.opened:
            warnings.warn(
                "write() called on non-opened interface.", flinter.InterfaceWarning
            )
            self.open()
        await self._awrite(*args, **kwargs)

    async def aread(self, *args, **kwargs):
        if not self.opened:
            warnings.warn(
                "read() called on non-opened interface.", flinter.InterfaceWarning
            )
            self.open()
        return await self._aread(*args, **kwargs)

    async def aquery(self, command, time_delay=0.1, **kwargs):
        if not self.opened:
            warnings.warn(
                "query() called on non-opened interface.", flinter.InterfaceWarning
            )
            self.open()
        return await self._aquery(command, **kwargs)

    async def await_for_srq(self, timeout=None):
        async with self.lock:
            await self.loop.run_in_executor(None, self.wait_for_srq, timeout)
