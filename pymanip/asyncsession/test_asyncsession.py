import os
import asyncio
import pytest
import numpy as np
from pymanip.asyncsession import AsyncSession


def test_logged_variables():
    async def task(sesn):
        sesn.add_entry(a=sesn.a)
        sesn.a = sesn.a + 1
        await asyncio.sleep(0.001)
        if sesn.a == 4:
            sesn.ask_exit()

    async def main(sesn):
        await sesn.monitor(task, server_port=None)

    with AsyncSession() as sesn:
        sesn.a = 0
        asyncio.run(main(sesn))
        # Test that sesn.logged_variable('varname') is equivalent to sesn['varname']
        # and returns timestamps and values
        ta, va = sesn.logged_variable("a")
        tta, vva = sesn["a"]
        assert (ta == tta).all()
        assert (va == vva).all()
        assert (va == [0, 1, 2, 3]).all()
        # Test the other methods
        assert sesn.logged_variables() == set("a")
        data = sesn.logged_data()
        dta, vta = data["a"]
        assert (dta == ta).all()
        assert (vta == va).all()
        assert sesn.logged_first_values() == {"a": (ta[0], 0)}
        assert sesn.logged_last_values() == {"a": (ta[-1], 3)}
        ttta, vvva = sesn.logged_data_fromtimestamp("a", sesn.t0)
        assert (ttta == ta).all()
        assert (vvva == va).all()


def test_run_monitor_equivalence():
    async def task(sesn):
        await asyncio.sleep(0.001)
        sesn.toto = 1
        sesn.ask_exit()

    async def main(sesn):
        await sesn.monitor(task, server_port=None)

    with AsyncSession() as sesn:
        sesn.toto = 0
        asyncio.run(main(sesn))
        assert sesn.toto == 1

    with AsyncSession() as sesn:
        sesn.toto = 0
        sesn.run(task, server_port=None)
        assert sesn.toto == 1


def test_parameters(tmpdir):
    async def dummy(sesn):
        sesn.ask_exit()
        await asyncio.sleep(0.001)

    with AsyncSession(os.path.join(tmpdir, "test_asyncsession")) as sesn:
        params = {"c": 3e8, "pi": 3.14}
        sesn.save_parameter(params, a=1, b=2)
        sesn.save_parameter(d=10)
        sesn.run(dummy, server_port=None)

    sesn = None

    with AsyncSession(os.path.join(tmpdir, "test_asyncsession")) as sesn:
        a = sesn.parameter("a")
        params = sesn.parameters()

        assert sesn.has_parameter("pi")

        b = params["b"]
        c = params["c"]
        pi = params["pi"]
        d = params["d"]

        assert a == 1
        assert b == 2
        assert c == 3e8
        assert pi == 3.14
        assert d == 10


def test_datasets():
    async def task(sesn):
        sesn.add_dataset(a=[1, 2, 3, 4])
        sesn.add_dataset(c=[1, 2, 3])
        await asyncio.sleep(0.001)
        sesn.add_dataset(b=np.array([5, 6, 7, 8]))
        sesn.add_dataset(c=[4, 5, 6])
        sesn.ask_exit()

    with AsyncSession() as sesn:
        sesn.run(task, server_port=None)
        assert sesn.dataset("a") == [1, 2, 3, 4]
        assert (sesn.dataset("b") == (5, 6, 7, 8)).all()
        for ts, d_a in sesn.datasets("a"):
            assert d_a == [1, 2, 3, 4]
        assert sesn.dataset_names() == {"a", "b", "c"}
        t_a, d_a = sesn.dataset_last_data("a")
        assert d_a == [1, 2, 3, 4]
        t_a = sesn.dataset_times("a")[0]
        t_b = sesn.dataset_times("b")[0]
        assert t_b - t_a >= 0.001
        t_last, data_last = sesn.dataset_last_data("c")
        assert data_last == [4, 5, 6]
