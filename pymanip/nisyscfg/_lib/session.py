"""

Function definition for intiating and closing sessions and search sessions:
- NISysCfgInitializeSession
- NISysCfgFindHardware
- NISysCfgNextResource
- NISysCfgCloseHandle

"""

import ctypes

from pymanip.nisyscfg._lib import lib
from pymanip.nisyscfg._lib.types import NISysCfgEnumExpertHandle, NISysCfgSessionHandle
from pymanip.nisyscfg._lib.constants import (
    NISysCfgLocale,
    NISysCfgFilterMode,
    NISysCfgStatus,
)


def NISysCfgInitializeSession(
    target="localhost",
    user=None,
    password=None,
    lang=NISysCfgLocale.Default,
    force_refresh=False,
    connect_timeout=1000,
):
    if isinstance(target, str):
        target = target.encode("ascii")
    if isinstance(user, str):
        user = user.encode("ascii")
    if isinstance(password, str):
        password = password.encode("ascii")
    f = lib.NISysCfgInitializeSession
    f.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
        ctypes.POINTER(NISysCfgEnumExpertHandle),
        ctypes.POINTER(NISysCfgSessionHandle),
    )
    f.restype = ctypes.c_ulong
    expertHdl = NISysCfgEnumExpertHandle(0)
    sesnHdl = NISysCfgSessionHandle(0)
    status = f(
        target,
        user,
        password,
        lang,
        force_refresh,
        connect_timeout,
        ctypes.byref(expertHdl),
        ctypes.byref(sesnHdl),
    )
    return NISysCfgStatus(status), expertHdl, sesnHdl


def NISysCfgFindHardware(
    sesnHandle,
    filterMode=NISysCfgFilterMode.MatchValuesAll,
    filterHandle=None,
    expert_names=None,
):
    f = lib.NISysCfgFindHardware
    f.argtypes = (
        NISysCfgSessionHandle,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_char_p,
        ctypes.POINTER(ctypes.c_void_p),
    )
    f.restype = ctypes.c_ulong
    resourceEnumHandle = ctypes.c_void_p(0)
    status = f(
        sesnHandle,
        filterMode,
        filterHandle,
        expert_names,
        ctypes.byref(resourceEnumHandle),
    )
    return NISysCfgStatus(status), resourceEnumHandle


def NISysCfgNextResource(sesnHandle, resourceEnumHandle):
    f = lib.NISysCfgNextResource
    f.argtypes = (
        NISysCfgSessionHandle,
        ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_void_p),
    )
    f.restype = ctypes.c_ulong
    resourceHandle = ctypes.c_void_p(0)
    status = f(sesnHandle, resourceEnumHandle, ctypes.byref(resourceHandle))
    return NISysCfgStatus(status), resourceHandle


def NISysCfgCloseHandle(handle):
    f = lib.NISysCfgCloseHandle
    f.argtypes = (ctypes.c_void_p,)
    f.restype = ctypes.c_ulong
    status = f(handle)
    return NISysCfgStatus(status)
