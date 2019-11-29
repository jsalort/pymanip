Task management
===============

The main entry point for an experimental session is the :meth:`pymanip.asyncsession.AsyncSession.monitor` function which should be awaited from the main function of the program. The typical main structure of a program is then:

.. code-block:: python

    async def monitoring_task(sesn):
        some_value = await sesn.some_device.aget()
        sesn.add_entry(some_value=some_value)
        await sesn.sleep(10)

    async def main(sesn):
        async with SomeDevice() as sesn.some_device:
            await sesn.monitor(monitoring_task)

    with AsyncSession() as sesn:
        asyncio.run(main(sesn))

In this example, we see the use of the context managers, both for the :class:`AsyncSession` object,
and for the instrument object. The main experimental measurement lies in the :func:`monitoring_task` function, which should not be an explicit `for` loop. Indeed, the :meth:`sesn.monitor` method will implement the `for` loop, with checks for the interruption signal.

Possible additionnal initialisation of devices can be added to the :func:`main` function. Possible additionnal initalisation of session variables can be added in the `with AsyncSession()` block.
Note that all functions take the session object as its first argument. It is therefore possible to write the same code as a subclass of :class:`AsyncSession`, but this is not strictly necessary, i.e.

.. code-block:: python

    class Monitoring(AsyncSession):

        async def monitoring_task(self):
            some_value = await self.some_device.aget()
            self.add_entry(some_value=some_value)
            await self.sleep(10)

        async def main(self):
            async with SomeDevice() as self.some_device:
                await self.monitor(self.monitoring_task)

    with Monitoring() as mon:
        asyncio.run(mon.main())

The benefits of the asynchronous structure of the example program is clearer when plotting tasks,
and email tasks are added, or when there are several concurrent monitoring tasks. The :func:`main`
function may then become:

.. code-block:: python

    async def main(sesn):
        async with SomeDevice() as sesn.some_device:
            await sesn.monitor(monitoring_task_a,
                               monitoring_task_b,
                               sesn.plot(['var_a', 'var_b', 'var_c']),
                               sesn.send_email(from_addr='toto@titi.org',
                                               to_addrs='tata@titi.org',
                                               delay_hours=2.0),
                               )

The useful pre-defined tasks are :meth:`pymanip.asyncsession.AsyncSession.send_email`, :meth:`pymanip.asyncsession.AsyncSession.plot` and :meth:`pymanip.asyncsession.AsyncSession.sweep`.
