import ctypes
from ctypes.util import find_library

cdll = ctypes.cdll.LoadLibrary(find_library("nidaqmx"))


def DAQmxGetSysDevNames():
    f = cdll.DAQmxGetSysDevNames
    f.argtypes = (ctypes.c_char_p, ctypes.c_uint32)
    f.restype = ctypes.c_int32
    bufsize = 1024
    buf = ctypes.create_string_buffer(bufsize)
    status = f(buf, bufsize)
    return status, buf.value.decode("ascii")


def DAQmxGetSysGlobalChans():
    f = cdll.DAQmxGetSysGlobalChans
    f.argtypes = (ctypes.c_char_p, ctypes.c_uint32)
    f.restype = ctypes.c_int32
    bufsize = 1024
    buf = ctypes.create_string_buffer(bufsize)
    status = f(buf, bufsize)
    return status, buf.value.decode("ascii")


status, devnames = DAQmxGetSysDevNames()
print(status)
print(devnames)

status, globalchans = DAQmxGetSysGlobalChans()
print(status)
print(globalchans)
