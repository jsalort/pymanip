"""

NI System Configuration DLL finding

"""

import ctypes
from ctypes.util import find_library
import os

libpath = find_library("nisyscfg")
if os.name == "posix":
    lib = ctypes.cdll.LoadLibrary(libpath)
elif os.name == "nt":
    lib = ctypes.windll.LoadLibrary(libpath)
