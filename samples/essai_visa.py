import ctypes
from enum import IntEnum

_VI_ERROR = -2147483648

class VisaStatus(IntEnum):
    VI_SUCCESS = 0
    VI_ERROR_INV_OBJECT = _VI_ERROR+0x3FFF000E
    VI_ERROR_NSUP_OPER = _VI_ERROR+0x3FFF0067
    VI_ERROR_INV_EXPR = _VI_ERROR+0x3FFF0010
    VI_ERROR_RSRC_NFOUD = _VI_ERROR+0x3FFF0011
    VI_ERROR_CLOSING_FAILED = _VI_ERROR+0x3FFF0016
    VI_WARN_NULL_OBJECT = 0x3FFF0082


visa = ctypes.cdll.LoadLibrary('/usr/local/vxipnp/linux/bin/libvisa.so.7')
ViObject = ctypes.c_uint32
ViSession = ViObject
ViStatus = ctypes.c_int32

def viOpenDefaultRM():
    f = visa.viOpenDefaultRM
    f.argtypes = (ctypes.POINTER(ViSession),)
    f.restype = ViStatus
    sesn = ViSession(0)
    status = VisaStatus(f(ctypes.byref(sesn)))
    return status, sesn

def viFindRsrc(sesn, expr):
    if isinstance(expr, str):
        expr = expr.encode('ascii')
    f = visa.viFindRsrc
    f.argtypes = (ViSession, ctypes.c_char_p, ctypes.POINTER(ViObject), ctypes.POINTER(ctypes.c_uint32),
                  ctypes.c_char_p)
    f.restype = ViStatus
    findList = ViObject(0)
    retcnt = ctypes.c_uint32(0)
    instrDesc = ctypes.create_string_buffer(256)
    status = f(sesn, expr, ctypes.byref(findList), ctypes.byref(retcnt), instrDesc)
    return VisaStatus(status), findList, retcnt.value, instrDesc.value.decode('ascii')

def viFindNext(sesn, findList):
    f = visa.viFindNext
    f.argtypes = (ViObject, ctypes.c_char_p)
    f.restype = ViStatus
    instrDesc = ctypes.create_string_buffer(256)
    status = f(findList, instrDesc)
    return VisaStatus(status), instrDesc.value.decode('ascii')

def viClose(viobj):
    f = visa.viClose
    f.argtypes = (ViObject,)
    f.restype = ViStatus
    status = f(viobj)
    return VisaStatus(status)

status, rm = viOpenDefaultRM()
if status == VisaStatus.VI_SUCCESS:
    try:
        status, findList, retcnt, instrDesc = viFindRsrc(rm, "?*")
        if status == VisaStatus.VI_SUCCESS:
            try:
                print(instrDesc)
                for _ in range(retcnt-1):
                    status, instrDesc = viFindNext(rm, findList)
                    if status == VisaStatus.VI_SUCCESS:
                        print(instrDesc)
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
