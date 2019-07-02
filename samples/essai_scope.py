import ctypes
from ctypes.util import find_library
import os
import platform
import essai_visa as visa

arch = platform.architecture()[0]
if arch.startswith("64"):
    libname = "niScope_64"
else:
    libname = "niScope_32"
lib = find_library(libname)
if os.name == "posix":
    libniScope = ctypes.cdll.LoadLibrary(lib)
elif os.name == "nt":
    libniScope = ctypes.windll.LoadLibrary(lib)


def niScope_init(rsrcName, IDQuery=True, resetDevice=False):
    if isinstance(rsrcName, str):
        rsrcName = rsrcName.encode("ascii")
    f = libniScope.niScope_init
    f.argtypes = (
        ctypes.c_char_p,
        visa.ViBoolean,
        visa.ViBoolean,
        ctypes.POINTER(visa.ViSession),
    )
    f.restype = visa.ViStatus
    vi = visa.ViSession(0)
    status = f(rsrcName, IDQuery, resetDevice, ctypes.byref(vi))
    return visa.VisaStatus(status), vi


def niScope_close(vi):
    f = libniScope.niScope_close
    f.argtypes = (visa.ViSession,)
    f.restype = visa.ViStatus
    status = f(vi)
    return visa.VisaStatus(status)


for rsrc in ("PXI2::15::INSTR", "PXI2::14::INSTR", "Dev2", "Dev3"):
    print(rsrc)
    status, vi = niScope_init(rsrc)
    print(status)
    if status == visa.VisaStatus.VI_SUCCESS:
        status, val = visa.viGetAttribute_String(
            vi, visa.VisaAttribute.IVI_ATTR_LOGICAL_NAME
        )
        print(status, val)
        status = niScope_close(vi)
