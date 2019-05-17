import warnings

from .session import NISysCfgSession
from ._lib.session import (
    NISysCfgFindHardware,
    NISysCfgCloseHandle,
    NISysCfgNextResource,
)
from ._lib.properties import (
    NISysCfgGetResourceProperty,
    NISysCfgGetResourceIndexedProperty,
)
from ._lib.constants import NISysCfgResourceProperty, NISysCfgStatus


class NISysCfgResourceAttributeError(AttributeError):
    def __init__(self, description, status):
        self.status = status
        super(NISysCfgResourceAttributeError, self).__init__(description)


class NISysCfgResource:
    def __init__(self, resourceHandle):
        self.resourceHandle = resourceHandle

    def close(self):
        if self.resourceHandle:
            status = NISysCfgCloseHandle(self.resourceHandle)
            if status != NISysCfgStatus.OK:
                raise RuntimeError(
                    f"NISysCfgCloseHandle failed. Status: {str(status):}."
                )
            self.resourceHandle = None
        else:
            warnings.warn("close was called twice on NISysCfgResource!")

    def __del__(self):
        if self.resourceHandle is not None:
            warnings.warn("NISysCfgResource was left open!", RuntimeWarning)
            self.close()

    def __getattr__(self, key):
        status, val = NISysCfgGetResourceProperty(
            self.resourceHandle, getattr(NISysCfgResourceProperty, key)
        )
        if status == NISysCfgStatus.OK:
            return val
        raise NISysCfgResourceAttributeError(
            f"NISysCfgGetResourceProperty returned {str(status):}.", status
        )

    def indexed_properties(self):
        return NISysCfgGetResourceIndexedProperty(self.resourceHandle)


class _NISysCfgHardwareEnumerator:
    def __init__(self, sesn):
        self.sesn = sesn
        self.resourceEnumHandle = None

    def __enter__(self):
        status, resourceEnumHandle = NISysCfgFindHardware(self.sesn.sessionHandle)
        if status != NISysCfgStatus.OK:
            raise RuntimeError(f"NISysCfgFindHardware failed. Status: {str(status):}.")
        self.resourceEnumHandle = resourceEnumHandle
        return self

    def __exit__(self, type_, value, cb):
        if self.resourceEnumHandle:
            status = NISysCfgCloseHandle(self.resourceEnumHandle)
            if status != NISysCfgStatus.OK:
                raise RuntimeError(
                    f"NISysCfgCloseHandle failed. Status: {str(status):}."
                )

    def next_resource(self):
        status, resourceHandle = NISysCfgNextResource(
            self.sesn.sessionHandle, self.resourceEnumHandle
        )
        if status == NISysCfgStatus.OK and resourceHandle:
            return NISysCfgResource(resourceHandle)
        else:
            return None


def NISysCfgHardwareEnumerator():
    with NISysCfgSession() as sesn, _NISysCfgHardwareEnumerator(sesn) as enum:

        while True:
            res = enum.next_resource()
            if res:
                yield res
            else:
                break
