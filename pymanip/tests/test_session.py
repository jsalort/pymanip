import os
import pytest
import pymanip.session as sess


def test_name_generator():
    """

    Test the name generator

    """

    name1 = sess.makeAcqName()
    name2 = sess.makeAcqName()
    assert name1 != name2


def test_log_addline(tmpdir):
    """

    Test the log_addline function

    """

    with sess.Session(os.path.join(tmpdir, "test_session"), ("a", "b", "c")) as sesn:
        for a in range(5):
            b = a ** 2
            c = 2 * b  # noqa: F841
            sesn.log_addline()

    with sess.SavedSession(os.path.join(tmpdir, "test_session")) as sesn:
        assert tuple(sesn.log_variable_list()) == ("a", "b", "c")
        assert sesn.has_log("a")
        assert sesn.has_log("b")
        assert sesn.has_log("c")
        assert (sesn["a"] == (0, 1, 2, 3, 4)).all()
        assert (sesn["b"] == (0, 1, 4, 9, 16)).all()
        assert (sesn["c"] == (0, 2, 8, 18, 32)).all()
        assert (sesn.log("a") == sesn["a"]).all()
        assert len(tuple(sesn.dataset_names())) == 0
        assert not sesn.has_parameter("toto")
        with pytest.raises(KeyError):
            sesn["toto"]


def test_cache(tmpdir):
    """

    Test the SavedSession cache system

    """

    # Create a dummy session
    with sess.Session(os.path.join(tmpdir, "test_session"), ("a", "b", "c")) as sesn:
        for a in range(5):
            b = a ** 2
            c = 2 * b  # noqa: F841
            sesn.log_addline()

    # Test the cache
    with sess.SavedSession(
        os.path.join(tmpdir, "test_session"), cache_location=tmpdir
    ) as sesn:
        assert len(tuple(sesn.cachedvars)) == 0
        assert not sesn.cached("toto")
        with pytest.raises(KeyError):
            sesn.cachedvalue("toto")
        toto = [10, 13, 15]  # noqa: F841
        sesn.cache("toto")

    sesn = None

    with sess.SavedSession(
        os.path.join(tmpdir, "test_session"), cache_location=tmpdir
    ) as sesn:
        assert tuple(sesn.cachedvars) == ("toto",)
        assert sesn.cached("toto")
        assert (sesn.cachedvalue("toto") == [10, 13, 15]).all()
        with pytest.raises(KeyError):
            sesn["toto"]
