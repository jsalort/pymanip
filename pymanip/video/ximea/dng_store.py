"""Wrapper for Ximea DNG Store API
==================================

"""

import ctypes
import ctypes.wintypes as wintypes  # noqa: F401

from ximea.xidefs import XI_COLOR_FILTER_ARRAY  # noqa: F401

xiapi_dng_store = ctypes.CDLL(r"C:\XIMEA\DNG Store\binX64\xiapi_dng_store.dll")
