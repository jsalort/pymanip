import os
import asyncio
import pytest
import numpy as np
from pymanip.aiosession import AsyncSession
from pymanip.asyncsession import SavedAsyncSession


@pytest.mark.asyncio
async def test_logged_variables():
    async def task(sesn):
        await sesn.add_entry(a=sesn.a)
        sesn.a = sesn.a + 1
        await asyncio.sleep(0.001)
        if sesn.a == 4:
            sesn.ask_exit()

    async def main(sesn):
        await sesn.monitor(task, server_port=None)

    async with AsyncSession() as sesn:
        sesn.a = 0
        await sesn.monitor(task, server_port=None)
        # Test that sesn.logged_variable('varname') is equivalent to sesn['varname']
        # and returns timestamps and values
        ta, va = await sesn.logged_variable("a")
        assert (va == [0, 1, 2, 3]).all()
        assert (await sesn.logged_variables()) == set("a")
        data = await sesn.logged_data()  # noqa: F841
        assert (await sesn.logged_first_values()) == {"a": (ta[0], 0)}
        assert (await sesn.logged_last_values()) == {"a": (ta[-1], 3)}
        ttta, vvva = await sesn.logged_data_fromtimestamp("a", (await sesn.t0()))
        assert (ttta == ta).all()
        assert (vvva == va).all()


@pytest.mark.asyncio
async def test_parameters(tmp_path):
    async def dummy(sesn):
        sesn.ask_exit()
        await asyncio.sleep(0.001)

    tmp_path.mkdir(exist_ok=True)

    async with AsyncSession(tmp_path / "test_asyncsession.db") as sesn:
        params = {"c": 3e8, "pi": 3.14}
        await sesn.save_parameter(params, a=1, b=2)
        await sesn.save_parameter(d=10)
        await sesn.monitor(dummy, server_port=None)

    sesn = None

    async with AsyncSession(tmp_path / "test_asyncsession.db") as sesn:
        a = await sesn.parameter("a")
        params = await sesn.parameters()

        assert await sesn.has_parameter("pi")

        b = params["b"]
        c = params["c"]
        pi = params["pi"]
        d = params["d"]

        assert a == 1
        assert b == 2
        assert c == 3e8
        assert pi == 3.14
        assert d == 10


@pytest.mark.asyncio
async def test_metadata(tmp_path):
    async def dummy(sesn):
        sesn.ask_exit()
        await asyncio.sleep(0.001)

    tmp_path.mkdir(exist_ok=True)

    async with AsyncSession(tmp_path / "test_asyncsession_meta.db") as sesn:
        await sesn.save_metadata(desc="toto")
        await sesn.monitor(dummy, server_port=None)

    sesn = SavedAsyncSession(tmp_path / "test_asyncsession_meta.db")
    assert sesn.metadata("desc") == "toto"


@pytest.mark.asyncio
async def test_datasets():
    async def task(sesn):
        await sesn.add_dataset(a=[1, 2, 3, 4])
        await sesn.add_dataset(c=[1, 2, 3])
        await asyncio.sleep(0.01)
        await sesn.add_dataset(b=np.array([5, 6, 7, 8]))
        await sesn.add_dataset(c=[4, 5, 6])
        sesn.ask_exit()

    async with AsyncSession() as sesn:
        await sesn.monitor(task, server_port=None)
        assert (await sesn.dataset("a")) == [1, 2, 3, 4]
        assert ((await sesn.dataset("b")) == (5, 6, 7, 8)).all()
        async for ts, d_a in sesn.datasets("a"):
            assert d_a == [1, 2, 3, 4]
        assert (await sesn.dataset_names()) == {"a", "b", "c"}
        t_a, d_a = await sesn.dataset_last_data("a")
        assert d_a == [1, 2, 3, 4]
        t_a = (await sesn.dataset_times("a"))[0]
        t_b = (await sesn.dataset_times("b"))[0]
        assert t_b - t_a >= 0.001
        t_last, data_last = await sesn.dataset_last_data("c")
        assert data_last == [4, 5, 6]


@pytest.mark.asyncio
async def test_delay_save(tmpdir):
    async def task(sesn):
        for a in range(50):
            await sesn.add_entry(a=a)
            await asyncio.sleep(0.001)
        sesn.ask_exit()

    async with AsyncSession(
        os.path.join(tmpdir, "test_delay"), delay_save=True
    ) as sesn:
        await sesn.monitor(task, server_port=None)

    sesn = SavedAsyncSession(os.path.join(tmpdir, "test_delay"))
    ts, a = sesn["a"]
    assert (a == np.array(list(range(50)))).all()

    async with AsyncSession(
        os.path.join(tmpdir, "test_delay"), delay_save=True
    ) as sesn:
        ts, a = await sesn.logged_variable("a")
        assert (a == np.array(list(range(50)))).all()
        await sesn.monitor(task, server_port=None)
        ts, a = await sesn.logged_variable("a")
        assert (a == np.array(list(range(50)) * 2)).all()

    SavedAsyncSession.cache_clear()
    sesn = SavedAsyncSession(os.path.join(tmpdir, "test_delay"))
    ts, a = sesn["a"]
    assert (a == np.array(list(range(50)) * 2)).all()
