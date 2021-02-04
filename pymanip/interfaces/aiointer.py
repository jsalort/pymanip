"""Asynchronous extension of :class:`fluidlab.interfaces.QueryInterface` (:mod:`pymanip.interfaces.aiointer`)
=============================================================================================================

This module defines :class:`AsyncQueryInterface` as the default subclass for :class:`fluidlab.interfaces.QueryInterface`.
The default implementation simply runs the methods of :class:`QueryInterface` into an executor, therefore in a separate thread. Because the parent class is probably not thread-safe, each call is protected by a lock to prevent concurrent calls to the instrument. However, the main thread is released and other tasks can be run on other instruments.

The methods that are defined in this way are :meth:`__aenter__`, :meth:`__aexit__`, :meth:`_aread`, :meth:`_awrite`, :meth:`_aquery` and :meth:`await_for_srq`. The higher lever co-routine methods :meth:`aread`, :meth:`awrite` and :meth:`aquery` simply checks that the interface is opened, and then awaits the low-level method, in a similar fashion as in the :class:`QueryInterface` class.

Therefore, concrete subclass such as :class:`pymanip.interfaces.aioserial.AsyncSerialInterface`, or :class:`pymanip.interfaces.aiovisa.AsyncVISAInterface` only have to override the low-level co-routine methods (if necessary).

.. autoclass:: AsyncQueryInterface
   :members:
   :private-members:

"""

import warnings
import asyncio
import fluidlab.interfaces as flinter
import functools
from time import monotonic


class AsyncQueryInterface(flinter.QueryInterface):
    """This class represents an asynchronous Query interface. It is a subclass of the synchronous
    QueryInterface defined in FluidLab. The input parameters are those of QueryInterface.

    Concrete subclasses may replace the :attr:`lock` attribute, and replace it by a global board lock if necessary.
    """

    def __init__(self):
        """Constructor method
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
        """Asynchronous context manager enter method
        """
        async with self.lock:
            return await self.loop.run_in_executor(None, self.__enter__)

    async def __aexit__(self, type_, value, tb):
        """Asynchronous context manager exit method
        """
        async with self.lock:
            await self.loop.run_in_executor(None, self.__exit__, type_, value, tb)

    async def _awrite(self, *args, **kwargs):
        """Low-level co-routine to send data to the instrument. This method does not check whether the interface
        is opened.
        In this basic class, it simply acquires the interface lock and runs the :meth:`_write` method in an executor.
        """
        async with self.lock:
            await self.loop.run_in_executor(
                None, self._write, *args
            )  # must be rewritten if necessary in concrete class

    async def _aread(self, *args, **kwargs):
        """Low-level co-routine to read data from the instrument. This method does not check whether the interface
        is opened.
        In this basic class, it simply acquires the interface lock and runs the :meth:`_read` method in an executor.
        """
        async with self.lock:
            data = await self.loop.run_in_executor(None, self._read, *args)
        return data

    async def _aquery(self, command, time_delay=0.1, **kwargs):
        """Low-level co-routine to write/read a query. This method does not check whether the interface is opened.
        There are two cases:

        - if the QueryInterface has a :meth:`_query` method, then the interface lock is acquired and the :meth:`_query` method is run in an executor;

        - otherwise, the :meth:`awrite` and :meth:`aread` co-routine methods are used.

        """

        if hasattr(self, "_query"):
            query_func = functools.partial(
                self.query, command, time_delay=time_delay, **kwargs
            )
            async with self.lock:
                return await self.loop.run_in_executor(None, query_func)
        else:
            if hasattr(self, "timeout"):
                timeout = self.timeout
            elif "timeout" in kwargs:
                timeout = kwargs["timeout"]
            else:
                timeout = 60.0

            if timeout < 10:
                timeout = 10.0

            await self.awrite(command)
            start = monotonic()
            while True:
                await asyncio.sleep(time_delay)
                data = await self.aread(**kwargs)
                if data:
                    return data
                elif monotonic() - start > timeout:
                    print("timeout")
                    break
                await asyncio.sleep(9 * time_delay)

    async def awrite(self, *args, **kwargs):
        """This co-routine method writes data to the instrument. The parameters are identical to the
        :meth:`write` method.
        """
        if not self.opened:
            warnings.warn(
                "write() called on non-opened interface.", flinter.InterfaceWarning
            )
            self.open()
        await self._awrite(*args, **kwargs)

    async def aread(self, *args, **kwargs):
        """This co-routine method reads data from the instrument. The parameters are identical to
        the :meth:`read` method.
        """
        if not self.opened:
            warnings.warn(
                "read() called on non-opened interface.", flinter.InterfaceWarning
            )
            self.open()
        return await self._aread(*args, **kwargs)

    async def aquery(self, command, time_delay=0.1, **kwargs):
        """This co-routine method queries the instrument. The parameters are identical to those of
        the :meth:`query` method.
        """
        if not self.opened:
            warnings.warn(
                "query() called on non-opened interface.", flinter.InterfaceWarning
            )
            self.open()
        return await self._aquery(command, time_delay=time_delay, **kwargs)
