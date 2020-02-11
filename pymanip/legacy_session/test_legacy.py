from importlib.resources import path

import numpy as np

from pymanip.legacy_session.octmi_binary import read_octave_binary, read_OctMI_session
from pymanip.legacy_session.octmi_dat import load_octmi_dat
import pymanip.legacy_session.example as example


def test_octave_binary():
    """

    Test reading from Octave binary file

    """

    with path(example, "essai.octave") as p:
        data = read_octave_binary(p)

    assert "A" in data
    assert "B" in data
    assert (data["A"] == np.array([1, 2, 3, 4])).all()
    assert (data["B"] == 2 * data["A"]).all()


def test_octmi_session():
    """

    Test reading from OctMI binary session file
    We need to use isclose() for the cosine test, because the exact
    result apparently depends on the platform (it would fail
    on travis, but pass on the Mac).

    """

    with path(example, "essai2_MIstate.octave") as p:
        dirpath = p.parent
        data = read_OctMI_session(str(dirpath / "essai2"))

    assert "startTime" in data
    assert "A" in data
    assert "B" in data
    assert "t" in data
    assert data["startTime"] == 1562334542.728428
    assert (data["A"] == np.arange(0.0, 5.1, 0.1)).all()
    assert np.isclose(data["B"], np.cos(data["A"])).all()
    assert data["t"].size == data["A"].size
    assert data["t"][0] > data["startTime"]


def test_octmi_dat():
    """

    Test reading from OctMI dat session file.
    We need to use np.isclose() because conversion to/from ascii may change
    one or two bits on the double precision numbers.

    """

    with path(example, "essai2_MI.dat") as p:
        dirpath = p.parent
        data = load_octmi_dat(str(dirpath / "essai2"))

    assert "Time" in data
    assert "A" in data
    assert "B" in data
    assert data["nval"] == 51
    assert np.isclose(data["A"], np.arange(0.0, 5.1, 0.1)).all()
    assert np.isclose(data["B"], np.cos(data["A"]), rtol=1e-4).all()
