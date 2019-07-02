import ctypes
from enum import IntEnum
from pathlib import Path

_VI_ERROR = -2147483648
IVI_STATUS_CODE_BASE = 0x3FFA0000
IVI_ERROR_BASE = _VI_ERROR + IVI_STATUS_CODE_BASE
IVI_SPECIFIC_ERROR_BASE = IVI_ERROR_BASE + 0x4000
IVI_ATTR_BASE = 1000000
IVI_ENGINE_PUBLIC_ATTR_BASE = IVI_ATTR_BASE + 50000


class VisaStatus(IntEnum):
    VI_SUCCESS = 0
    VI_ERROR_INV_OBJECT = _VI_ERROR + 0x3FFF000E
    VI_ERROR_NSUP_OPER = _VI_ERROR + 0x3FFF0067
    VI_ERROR_INV_EXPR = _VI_ERROR + 0x3FFF0010
    VI_ERROR_RSRC_NFOUD = _VI_ERROR + 0x3FFF0011
    VI_ERROR_CLOSING_FAILED = _VI_ERROR + 0x3FFF0016
    VI_ERROR_NSUP_ATTR = _VI_ERROR + 0x3FFF001D
    VI_ERROR_NSUP_ATTR_STATE = _VI_ERROR + 0x3FFF001E
    VI_ERROR_ATTR_READONLY = _VI_ERROR + 0x3FFF001F
    VI_ERROR_RSRC_LOCKED = _VI_ERROR + 0x3FFF000F
    VI_WARN_NULL_OBJECT = 0x3FFF0082
    VI_WARN_NSUP_ATTR_STATE = 0x3FFF0084
    NISCOPE_ERROR_NOT_A_SCOPE = IVI_SPECIFIC_ERROR_BASE + 0x022


class VisaAttribute(IntEnum):
    # UInt16
    VI_ATTR_PXI_BUS_NUM = 0x3FFF0205
    VI_ATTR_PXI_DEV_NUM = 0x3FFF0201
    VI_ATTR_PXI_CHASSIS = 0x3FFF0206
    VI_ATTR_FIND_RSRC_MODE = 0x3FFF0190
    VI_ATTR_SLOT = 0x3FFF00E8

    # Strings
    VI_ATTR_INTF_INST_NAME = 0xBFFF00E9
    VI_ATTR_MODEL_NAME = 0xBFFF0077
    VI_ATTR_PXI_SLOTPATH = 0xBFFF0207
    VI_ATTR_RSRC_NAME = 0xBFFF0002
    IVI_ATTR_LOGICAL_NAME = IVI_ENGINE_PUBLIC_ATTR_BASE + 305
    IVI_ATTR_IO_RESOURCE_DESCRIPTOR = IVI_ENGINE_PUBLIC_ATTR_BASE + 304


possible_paths = [
    Path("/usr/local/vxipnp/linux/bin/libvisa.so.7"),
    Path(r"C:\Windows\system32\visa64.dll"),
]
for visa_path in possible_paths:
    if visa_path.exists():
        break
else:
    raise RuntimeError("VISA library not found")

if visa_path.name.endswith("dll"):
    visa = ctypes.windll.LoadLibrary(str(visa_path))
else:
    visa = ctypes.cdll.LoadLibrary(str(visa_path))

ViObject = ctypes.c_uint32
ViSession = ViObject
ViStatus = ctypes.c_int32
ViAttr = ctypes.c_uint32
ViAttrState = ctypes.c_uint64
ViAccessMode = ctypes.c_uint32
ViBoolean = ctypes.c_uint16
VI_NULL = 0


def viOpenDefaultRM():
    f = visa.viOpenDefaultRM
    f.argtypes = (ctypes.POINTER(ViSession),)
    f.restype = ViStatus
    sesn = ViSession(0)
    status = VisaStatus(f(ctypes.byref(sesn)))
    return status, sesn


def viFindRsrc(sesn, expr):
    if isinstance(expr, str):
        expr = expr.encode("ascii")
    f = visa.viFindRsrc
    f.argtypes = (
        ViSession,
        ctypes.c_char_p,
        ctypes.POINTER(ViObject),
        ctypes.POINTER(ctypes.c_uint32),
        ctypes.c_char_p,
    )
    f.restype = ViStatus
    findList = ViObject(0)
    retcnt = ctypes.c_uint32(0)
    instrDesc = ctypes.create_string_buffer(256)
    status = f(sesn, expr, ctypes.byref(findList), ctypes.byref(retcnt), instrDesc)
    return VisaStatus(status), findList, retcnt.value, instrDesc.value.decode("ascii")


def viFindNext(sesn, findList):
    f = visa.viFindNext
    f.argtypes = (ViObject, ctypes.c_char_p)
    f.restype = ViStatus
    instrDesc = ctypes.create_string_buffer(256)
    status = f(findList, instrDesc)
    return VisaStatus(status), instrDesc.value.decode("ascii")


def viOpen(sesn, rsrcName, accessMode=VI_NULL, openTimeout=100):
    if isinstance(rsrcName, str):
        rsrcName = rsrcName.encode("ascii")
    f = visa.viOpen
    f.argtypes = (
        ViSession,
        ctypes.c_char_p,
        ViAccessMode,
        ctypes.c_uint32,
        ctypes.POINTER(ViObject),
    )
    f.restype = ViStatus
    vi = ViObject(0)
    status = f(sesn, rsrcName, accessMode, openTimeout, ctypes.byref(vi))
    return status, vi


def viClose(viobj):
    f = visa.viClose
    f.argtypes = (ViObject,)
    f.restype = ViStatus
    status = f(viobj)
    return VisaStatus(status)


def viGetAttribute(vi, attr, bufPtr):
    f = visa.viGetAttribute
    f.argtypes = (ViObject, ViAttr, ctypes.c_void_p)
    f.restype = ViStatus
    status = f(vi, attr, bufPtr)
    return VisaStatus(status)


def viGetAttribute_String(vi, attr):
    buf = ctypes.create_string_buffer(256)
    status = viGetAttribute(vi, attr, buf)
    return status, buf.value.decode("ascii")


def viGetAttribute_UInt16(vi, attr):
    buf = ctypes.c_uint16(0)
    status = viGetAttribute(vi, attr, ctypes.byref(buf))
    return status, buf.value


def viSetAttribute(vi, attr, val):
    f = visa.viSetAttribute
    f.argtypes = (ViObject, ViAttr, ViAttrState)
    f.restype = ViStatus
    status = f(vi, attr, val)
    return VisaStatus(status)


def describe(rm, instrDesc):
    print("Looking up attributes for", instrDesc)
    status, vi = viOpen(rm, instrDesc)
    if status == VisaStatus.VI_SUCCESS:
        try:
            for attr in (
                VisaAttribute.VI_ATTR_PXI_BUS_NUM,
                VisaAttribute.VI_ATTR_PXI_CHASSIS,
                VisaAttribute.VI_ATTR_PXI_DEV_NUM,
                VisaAttribute.VI_ATTR_SLOT,
            ):
                status, val = viGetAttribute_UInt16(vi, attr)
                if status == VisaStatus.VI_SUCCESS:
                    print(attr, val)
                else:
                    print(attr, status)
            for attr in (
                VisaAttribute.VI_ATTR_INTF_INST_NAME,
                VisaAttribute.VI_ATTR_MODEL_NAME,
                VisaAttribute.VI_ATTR_RSRC_NAME,
                VisaAttribute.IVI_ATTR_IO_RESOURCE_DESCRIPTOR,
            ):
                status, val = viGetAttribute_String(vi, attr)
                if status == VisaStatus.VI_SUCCESS:
                    print(attr, val)
                else:
                    print(attr, status)
        finally:
            viClose(vi)
    else:
        print(status)


def lookup():
    status, rm = viOpenDefaultRM()
    if status == VisaStatus.VI_SUCCESS:
        try:
            status, val = viGetAttribute_UInt16(
                rm, VisaAttribute.VI_ATTR_FIND_RSRC_MODE
            )
            print("FIND_RSRC_MODE", status, val)
            status = viSetAttribute(rm, VisaAttribute.VI_ATTR_FIND_RSRC_MODE, 32792)
            print(status)

            status, findList, retcnt, instrDesc = viFindRsrc(rm, "PXI?*::INSTR")
            if status == VisaStatus.VI_SUCCESS:
                try:
                    print(instrDesc)
                    describe(rm, instrDesc)
                    for _ in range(retcnt - 1):
                        status, instrDesc = viFindNext(rm, findList)
                        if status == VisaStatus.VI_SUCCESS:
                            print(instrDesc)
                            describe(rm, instrDesc)
                        else:
                            print(status)
                finally:
                    status = viClose(findList)
                    if status != VisaStatus.VI_SUCCESS:
                        print(status)
        finally:
            status = viClose(rm)
            if status != VisaStatus.VI_SUCCESS:
                print(status)


if __name__ == "__main__":
    lookup()
