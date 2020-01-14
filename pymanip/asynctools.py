import asyncio


def synchronize_generator(async_generator, *args, **kwargs):
    """
    Returns a synchronous generator from an asynchronous generator
    """

    ag = async_generator(*args, **kwargs)

    async def consume_generator(stop_signal):
        r = await ag.asend(stop_signal)
        return r

    loop = asyncio.get_event_loop()
    try:
        stop_signal = None
        while not stop_signal:
            val = loop.run_until_complete(consume_generator(stop_signal))
            stop_signal = yield val
        if stop_signal:
            val = loop.run_until_complete(consume_generator(stop_signal))
            yield val
    except StopAsyncIteration:
        pass


def synchronize_function(async_func, *args, **kwargs):
    """
    Execute synchronously an asynchronous function
    """

    try:
        r = asyncio.run(async_func(*args, **kwargs))
    except AttributeError:
        loop = asyncio.get_event_loop()
        r = loop.run_until_complete(async_func(*args, **kwargs))
    return r


if __name__ == "__main__":

    async def spam(n):
        for i in range(n):
            yield i ** n
            await asyncio.sleep(1.0)

    for x in synchronize_generator(spam, 3):
        print(x)

    async def f(x):
        for i in range(x):
            print(i)
            await asyncio.sleep(0.5)
        return i

    a = synchronize_function(f, 5)
    b = synchronize_function(f, 3)
    print(b)

    def sync_spam(n):
        yield from synchronize_generator(spam, n)

    for s in sync_spam(5):
        print(s)
