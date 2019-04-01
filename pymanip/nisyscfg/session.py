from ._lib.constants import NISysCfgLocale
from ._lib.session import NISysCfgInitializeSession, NISysCfgCloseHandle

class NISysCfgSession:

    def __init__(self, target='localhost', user=None, password=None, 
                 lang=NISysCfgLocale.Default, force_refresh=False, 
                 connect_timeout=1000):
        self.target = target
        self.user = user
        self.password = password
        self.lang = lang
        self.force_refresh = force_refresh
        self.connect_timeout = connect_timeout
        self.expertHandle = None
        self.sessionHandle = None
        
    def __enter__(self):
        status, expertHandle, sessionHandle = NISysCfgInitializeSession()
        if status != 0:
            raise RuntimeError('NISysCfgInitializeSession failed.')
        self.expertHandle = expertHandle
        self.sessionHandle = sessionHandle
        return self
        
    def __exit__(self, type_, value, cb):
        if self.expertHandle:
            status = NISysCfgCloseHandle(self.expertHandle)
            if status != 0:
                raise RuntimeError('NISysCfgCloseHandle failed.')
        if self.sessionHandle:
            status = NISysCfgCloseHandle(self.sessionHandle)
            if status != 0:
                raise RuntimeError('NISysCfgCloseHandle failed.')