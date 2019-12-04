"""

API to query properties on a given resource.
- NISysCfgGetResourceProperty
- NISysCfgGetResourceIndexedProperty

"""


import ctypes
from pymanip.nisyscfg._lib import lib
from pymanip.nisyscfg._lib.constants import (
    NISysCfgResourceProperty,
    NISysCfgIndexedProperty,
    NISYSCFG_SIMPLE_STRING_LENGTH,
    NISysCfgStatus,
)
from pymanip.nisyscfg._lib.types import NISysCfgResourcePropertyType


def NISysCfgGetResourceProperty(resourceHandle, propertyID):
    (
        attr_ctype,
        attr_ini,
        create_func,
        ref_func,
        enum_class,
    ) = NISysCfgResourcePropertyType[propertyID]
    if create_func is None:
        create_func = attr_ctype
    if ref_func == ctypes.byref:
        attr_func = ctypes.POINTER(attr_ctype)
    else:
        attr_func = attr_ctype
    f = lib.NISysCfgGetResourceProperty
    f.argtypes = (ctypes.c_void_p, ctypes.c_int, attr_func)
    f.restype = ctypes.c_ulong
    val = create_func(attr_ini)
    status = f(resourceHandle, propertyID, ref_func(val))
    try:
        val = val.value
        val = val.decode("ascii")
    except AttributeError:
        pass

    return NISysCfgStatus(status), val


def NISysCfgGetResourceIndexedProperty(resourceHandle):
    f = lib.NISysCfgGetResourceIndexedProperty
    f.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_char_p)
    f.restype = ctypes.c_ulong

    # implémenté seulement pour IndexedPropertyExpertName
    status, num_experts = NISysCfgGetResourceProperty(
        resourceHandle, NISysCfgResourceProperty.NumberOfExperts
    )
    if status != 0:
        raise RuntimeError(
            f"NISysCfgGetResourceProperty returned {str(NISysCfgStatus(status)):}"
        )
    data = list()
    for index in range(num_experts):
        indexed_data = dict()
        for attr in NISysCfgIndexedProperty:
            val = ctypes.create_string_buffer(NISYSCFG_SIMPLE_STRING_LENGTH)
            status = f(resourceHandle, attr, index, val)
            if status != 0:
                raise RuntimeError(
                    f"NISysCfgGetResourceIndexedProperty returned {str(NISysCfgStatus(status)):}"
                )
            indexed_data[attr.name] = val.value.decode("ascii")
        data.append(indexed_data)
    return data
